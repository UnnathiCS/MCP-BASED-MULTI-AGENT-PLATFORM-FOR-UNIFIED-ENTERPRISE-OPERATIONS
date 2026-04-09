"""
Email templates and formatting utilities for professional email responses.
"""

import os
from typing import Optional

def get_email_signature() -> str:
    """Get the professional email signature."""
    company_name = os.getenv("COMPANY_NAME", "CompanyZ")
    support_email = os.getenv("SUPPORT_EMAIL", "support@companyz.com")
    website = os.getenv("COMPANY_WEBSITE", "https://www.companyz.com")
    
    signature = f"""
---
{company_name} Support Team
Email: {support_email}
Website: {website}
"""
    return signature.strip()

def normalize_spacing(text: str) -> str:
    """
    Normalize spacing in text by reducing multiple newlines and trimming extra whitespace.
    """
    import re
    # Collapse 3+ newlines into 2 newlines (single paragraph break)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove trailing whitespace from lines
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    # Remove leading/trailing whitespace from text
    text = text.strip()
    return text

def convert_markdown_to_html(text: str) -> str:
    """
    Convert markdown formatting to HTML, removing markdown syntax.
    
    Args:
        text: Text with markdown formatting
    
    Returns:
        HTML formatted text
    """
    import re
    
    # Convert **text** to <strong>text</strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Convert *text* to <em>text</em> (italics)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    # Convert # Heading to <h3>Heading</h3>
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    # Convert - item to <li>item</li>
    text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    # Convert numbered lists
    text = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    
    return text

def format_html_email(body: str, customer_name: Optional[str] = None) -> str:
    """
    Format email body as HTML with professional styling.
    
    Args:
        body: Plain text email body (may contain markdown)
        customer_name: Optional customer name for personalization
    
    Returns:
        HTML formatted email
    """
    greeting = f"Dear {customer_name}," if customer_name else "Dear Customer,"

    # Normalize spacing and convert markdown to HTML
    normalized_body = normalize_spacing(body)
    html_body = convert_markdown_to_html(normalized_body)
    
    # Convert line breaks
    html_body = html_body.replace('\n\n', '</p><p>').replace('\n', '<br>')
    
    # Wrap in paragraph if not already wrapped
    if not html_body.startswith('<'):
        html_body = f'<p>{html_body}</p>'
    
    signature = get_email_signature()
    html_signature = signature.replace('\n', '<br>')
    
    html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            border-bottom: 2px solid #000;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .content {{
            margin: 20px 0;
        }}
        .signature {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
            color: #666;
        }}
        a {{
            color: #000;
            font-weight: bold;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        strong {{
            font-weight: bold;
            color: #000;
        }}
        h1, h2, h3 {{
            color: #000;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #000; font-weight: bold; margin: 0;">CompanyZ Support</h2>
    </div>
    <div class="content">
        <p>{greeting}</p>
        {html_body}
        <p>If you have any further questions, please don't hesitate to reach out.</p>
        <p>Best regards,<br>CompanyZ Support Team</p>
    </div>
    <div class="signature">
        {html_signature}
    </div>
</body>
</html>
"""
    return html_template

def remove_markdown_syntax(text: str) -> str:
    """
    Remove markdown syntax from text, keeping the content.
    
    Args:
        text: Text with markdown formatting
    
    Returns:
        Plain text without markdown syntax
    """
    import re
    
    # Remove **text** but keep text (make it stand out with ALL CAPS for emphasis in plain text)
    # Actually, just remove the ** and keep text as is for plain text
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # Remove *text* but keep text
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', text)
    # Remove # from headings
    text = re.sub(r'^#+\s*(.+)$', r'\1', text, flags=re.MULTILINE)
    # Remove - and numbers from list items
    text = re.sub(r'^[-*]\s+(.+)$', r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+(.+)$', r'\1', text, flags=re.MULTILINE)
    
    return text

def format_plain_email(body: str, customer_name: Optional[str] = None) -> str:
    """
    Format email body as plain text with signature.
    
    Args:
        body: Plain text email body (may contain markdown)
        customer_name: Optional customer name for personalization
    
    Returns:
        Formatted plain text email
    """
    greeting = f"Dear {customer_name}," if customer_name else "Dear Customer,"
    signature = get_email_signature()
    
    # Remove markdown syntax from body and normalize spacing
    clean_body = normalize_spacing(remove_markdown_syntax(body))
    
    formatted = f"""{greeting}

{clean_body}

If you have any further questions, please don't hesitate to reach out.

Best regards,
CompanyZ Support Team

{signature}
"""
    return formatted

