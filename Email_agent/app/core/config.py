import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
EMAIL_ADDRESS: str = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD") or os.getenv("EMAIL_PSSWORD", "")
IMAP_SERVER: str = os.getenv("IMAP_SERVER", "")
SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
SMTP_PORT: int = 587
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")

COMPANY_NAME: str = os.getenv("COMPANY_NAME", "CompanyZ")
SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "support@companyz.com")
COMPANY_WEBSITE: str = os.getenv("COMPANY_WEBSITE", "https://www.companyz.com")
