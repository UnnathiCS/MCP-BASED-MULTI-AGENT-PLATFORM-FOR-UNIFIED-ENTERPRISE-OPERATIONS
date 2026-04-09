from dotenv import load_dotenv
import os
import imaplib
import email
from email.header import decode_header

load_dotenv()

EMAIL = os.getenv("EMAIL_ADDRESS")
# Support both correct and misspelled variable
PASSWORD = os.getenv("EMAIL_PASSWORD") or os.getenv("EMAIL_PSSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER")

def fetch_unread_emails():
    """
    Fetches only unread emails from the inbox and marks them as read.
    """
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    status, messages = mail.search(None, 'UNSEEN')
    
    if status != 'OK':
        mail.logout()
        return []

    email_ids = messages[0].split()
    emails = []

    for eid in email_ids:
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

                email_data = {
                    "subject": subject,
                    "from": from_,
                    "body": body.strip(),
                    "message_id": msg.get("Message-ID"),
                    "in_reply_to": msg.get("In-Reply-To"),
                }
                emails.append(email_data)

                mail.store(eid, '+FLAGS', '\\Seen')

    mail.logout()
    return emails