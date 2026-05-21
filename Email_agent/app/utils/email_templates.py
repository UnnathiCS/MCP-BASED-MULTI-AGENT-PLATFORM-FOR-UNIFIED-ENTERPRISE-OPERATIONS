import re
from typing import Optional
from app.core.config import COMPANY_NAME, SUPPORT_EMAIL, COMPANY_WEBSITE


def get_email_signature() -> str:
    return f"---\n{COMPANY_NAME} Support Team\nEmail: {SUPPORT_EMAIL}\nWebsite: {COMPANY_WEBSITE}"


def normalize_spacing(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    return text.strip()


def format_support_response_body(body: str) -> str:
    if not body:
        return f"Thank you for contacting {COMPANY_NAME} Support."
    text = body.replace("\r\n", "\n").replace("\r", "\n").strip()
    text = re.sub(r'^\s*Subject\s*:\s*.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r'^\s*Relevant\s+Document\s+\d+\s*:\s*', '', text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r'^\s*---+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*Dear\s+[^,\n]+,\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(
        r'\n\s*(If you have any further questions[^\n]*)?\s*(Best regards|Regards|Sincerely|Thanks),?\s*\n(?:[^\n]*\n){0,4}\s*$',
        '', text, flags=re.IGNORECASE
    )
    text = re.sub(r'^\s*[\u2022\-]\s+', '- ', text, flags=re.MULTILINE)
    text = normalize_spacing(text)
    return text or f"Thank you for contacting {COMPANY_NAME} Support."


def format_html_email(body: str, customer_name: Optional[str] = None) -> str:
    greeting = f"Dear {customer_name}," if customer_name else "Dear Customer,"
    normalized = format_support_response_body(body)
    html_body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', normalized)
    html_body = html_body.replace('\n\n', '</p><p>').replace('\n', '<br>')
    if not html_body.startswith('<'):
        html_body = f'<p>{html_body}</p>'
    sig = get_email_signature().replace('\n', '<br>')
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;line-height:1.6;color:#333;max-width:600px;margin:0 auto;padding:20px}}
.header{{border-bottom:2px solid #000;padding-bottom:10px;margin-bottom:20px}}
.signature{{margin-top:30px;padding-top:20px;border-top:1px solid #ddd;font-size:.9em;color:#666}}
</style></head><body>
<div class="header"><h2 style="color:#000;margin:0">{COMPANY_NAME} Support</h2></div>
<div class="content"><p>{greeting}</p>{html_body}
<p>If you have any further questions, please don't hesitate to reach out.</p>
<p>Best regards,<br>{COMPANY_NAME} Support Team</p></div>
<div class="signature">{sig}</div></body></html>"""


def format_plain_email(body: str, customer_name: Optional[str] = None) -> str:
    greeting = f"Dear {customer_name}," if customer_name else "Dear Customer,"
    clean_body = normalize_spacing(re.sub(r'\*\*(.+?)\*\*', r'\1', format_support_response_body(body)))
    return f"""{greeting}\n\n{clean_body}\n\nIf you have any further questions, please don't hesitate to reach out.\n\nBest regards,\n{COMPANY_NAME} Support Team\n\n{get_email_signature()}\n"""
