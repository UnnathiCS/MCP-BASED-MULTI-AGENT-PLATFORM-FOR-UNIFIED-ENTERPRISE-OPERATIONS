import imaplib
import email
import smtplib
import re
import time
import logging
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid

from app.core.config import (
    EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER, SMTP_SERVER, SMTP_PORT
)
from app.utils.email_templates import format_html_email, format_plain_email

logger = logging.getLogger(__name__)


def fetch_unread_emails() -> list:
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    mail.select("inbox")
    status, messages = mail.search(None, 'UNSEEN')
    if status != 'OK':
        mail.logout()
        return []
    emails = []
    for eid in messages[0].split():
        _, msg_data = mail.fetch(eid, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                subject = subject.decode(encoding or 'utf-8') if isinstance(subject, bytes) else subject
                from_ = msg.get("From")
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors='ignore')
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors='ignore')
                emails.append({
                    "subject": subject, "from": from_, "body": body.strip(),
                    "message_id": msg.get("Message-ID"),
                    "in_reply_to": msg.get("In-Reply-To"),
                })
                mail.store(eid, '+FLAGS', '\\Seen')
    mail.logout()
    return emails


def extract_customer_name(from_email: str, email_body: str = "") -> str:
    match = re.search(r'([^<]+)<', from_email)
    if match:
        name = match.group(1).strip().strip('"').strip("'")
        if name and '@' not in name:
            return name.split()[0]
    if email_body:
        for pattern in [
            r'(?:Best regards|Regards|Thanks|Sincerely)[,\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*$',
        ]:
            match = re.search(pattern, email_body, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).split()[0]
    return None


def send_auto_reply(to_email, subject, body, original_message_id=None, in_reply_to=None, customer_name=None):
    if not customer_name:
        customer_name = extract_customer_name(to_email)
    msg = MIMEMultipart('alternative')
    msg["Subject"] = f"Re: {subject}" if not subject.startswith(("Re:", "RE:")) else subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Message-ID"] = make_msgid()
    if original_message_id:
        msg["In-Reply-To"] = original_message_id
        msg["References"] = f"{in_reply_to} {original_message_id}" if in_reply_to else original_message_id
    elif in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    msg.attach(MIMEText(format_plain_email(body, customer_name), 'plain', 'utf-8'))
    msg.attach(MIMEText(format_html_email(body, customer_name), 'html', 'utf-8'))
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, [to_email], msg.as_string())
        print(f"[↩] Auto-reply sent to {to_email}")


def retry_function(func, max_retries=3, initial_delay=1.0, backoff_factor=2.0, **kwargs):
    last_exception = None
    delay = initial_delay
    for attempt in range(max_retries + 1):
        try:
            return func(**kwargs) if kwargs else func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(f"Attempt {attempt+1}/{max_retries+1} failed for {func.__name__}: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(f"All {max_retries+1} attempts failed for {func.__name__}: {e}")
    raise last_exception
