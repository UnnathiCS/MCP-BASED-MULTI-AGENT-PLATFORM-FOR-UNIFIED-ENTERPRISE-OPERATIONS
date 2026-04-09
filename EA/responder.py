import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid
from dotenv import load_dotenv
from email_templates import format_html_email, format_plain_email
import re

load_dotenv()

EMAIL = os.getenv("EMAIL_ADDRESS")
# Support both correct and misspelled variable
PASSWORD = os.getenv("EMAIL_PASSWORD") or os.getenv("EMAIL_PSSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = 587 

def extract_customer_name(from_email: str, email_body: str = "") -> str:
    """
    Extract customer name from email address or email body.
    
    Args:
        from_email: Email address (e.g., "John Doe <john@example.com>")
        email_body: Optional email body to extract name from signature
    
    Returns:
        Customer name or None
    """
    # Try to extract from email address
    match = re.search(r'([^<]+)<', from_email)
    if match:
        name = match.group(1).strip().strip('"').strip("'")
        if name and '@' not in name:
            return name.split()[0]  # Return first name
    
    # Try to extract from email body signature
    if email_body:
        # Look for common patterns like "Best regards, John" or "Thanks, John Doe"
        patterns = [
            r'(?:Best regards|Regards|Thanks|Sincerely)[,\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*$',
        ]
        for pattern in patterns:
            match = re.search(pattern, email_body, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).split()[0]
    
    return None

def send_auto_reply(to_email, subject, body, original_message_id=None, in_reply_to=None, customer_name=None):
    """
    Send an auto-reply email with proper threading support, HTML formatting, and signature.
    
    Args:
        to_email: Recipient email address
        subject: Original email subject
        body: Response body text
        original_message_id: Message-ID of the original email (for threading)
        in_reply_to: In-Reply-To header from original email (for threading)
        customer_name: Optional customer name for personalization
    """
    # Extract customer name if not provided
    if not customer_name:
        customer_name = extract_customer_name(to_email)
    
    # Create multipart message (both HTML and plain text)
    msg = MIMEMultipart('alternative')
    
    # Handle subject - only add "Re:" if not already present
    if not subject.startswith("Re:") and not subject.startswith("RE:"):
        msg["Subject"] = f"Re: {subject}"
    else:
        msg["Subject"] = subject
    
    msg["From"] = EMAIL
    msg["To"] = to_email
    
    # Generate a new Message-ID for this reply
    new_message_id = make_msgid()
    msg["Message-ID"] = new_message_id
    
    # Maintain email threading
    if original_message_id:
        msg["In-Reply-To"] = original_message_id
        # Build References header - include original and any previous references
        if in_reply_to:
            msg["References"] = f"{in_reply_to} {original_message_id}"
        else:
            msg["References"] = original_message_id
    elif in_reply_to:
        # If we have In-Reply-To but no message_id, use it for threading
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    
    # Create both plain text and HTML versions
    plain_text = format_plain_email(body, customer_name)
    html_text = format_html_email(body, customer_name)
    
    # Attach both versions
    part1 = MIMEText(plain_text, 'plain', 'utf-8')
    part2 = MIMEText(html_text, 'html', 'utf-8')
    
    msg.attach(part1)
    msg.attach(part2)

    try:
        # Connect to SMTP server
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, [to_email], msg.as_string())
            print(f"[↩] Auto-reply sent to {to_email}")
    except Exception as e:
        print(f"[!] Failed to send auto-reply to {to_email}: {e}")
        raise
