import os
from zoneinfo import ZoneInfo


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PARIS = ZoneInfo("Europe/Paris")

DATABASE_URL = os.getenv("DATABASE_URL")
FMP_API_KEY = os.getenv("FMP_API_KEY", "")
CALENDAR_TZ = PARIS
APP_ENV = os.getenv("APP_ENV", "production").lower()
IS_PRODUCTION = APP_ENV == "production"

ACCOUNT_DB_PATH = os.path.join(PROJECT_ROOT, "terminal_users.db")
ACCOUNT_DB_BACKEND = "postgres" if DATABASE_URL else "sqlite"
SESSION_COOKIE = "tt_session"
TRIAL_DAYS = 7
OWNER_EMAILS = {
    email.strip().lower()
    for email in os.getenv("OWNER_EMAILS", os.getenv("OWNER_EMAIL", "")).split(",")
    if email.strip()
}
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD", "")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_MONTHLY = os.getenv("STRIPE_PRICE_MONTHLY", "")
STRIPE_PRICE_YEARLY = os.getenv("STRIPE_PRICE_YEARLY", "")
STRIPE_PRICE_LIFETIME = os.getenv("STRIPE_PRICE_LIFETIME", "")
STRIPE_ALLOWED_WEBHOOK_EVENTS = {
    "checkout.session.completed",
    "invoice.paid",
    "invoice.payment_failed",
    "customer.subscription.updated",
    "customer.subscription.deleted",
}
STRIPE_WEBHOOK_MAX_BYTES = 512 * 1024

APP_BASE_URL = os.getenv("APP_BASE_URL", "https://xauterminal.com").rstrip("/")
LEGAL_BUSINESS_NAME = os.getenv("LEGAL_BUSINESS_NAME", "MDTrading")
LEGAL_PUBLISHER_NAME = os.getenv("LEGAL_PUBLISHER_NAME", "Marc Debiais")
LEGAL_CONTACT_EMAIL = os.getenv("LEGAL_CONTACT_EMAIL", "mdtrading@xauterminal.com")
LEGAL_BUSINESS_ADDRESS = os.getenv("LEGAL_BUSINESS_ADDRESS", "42 Av. de Bordeaux, 86130 Jaunay-Marigny, France")
LEGAL_BUSINESS_ID = os.getenv("LEGAL_BUSINESS_ID", "SIREN 824468789")
LEGAL_HOSTING_PROVIDER = os.getenv("LEGAL_HOSTING_PROVIDER", "Render")

EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587")) if os.getenv("EMAIL_SMTP_PORT") else 0
EMAIL_SMTP_USER = os.getenv("EMAIL_SMTP_USER", "")
EMAIL_SMTP_PASSWORD = os.getenv("EMAIL_SMTP_PASSWORD", "")
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", f"noreply@{os.getenv('EMAIL_DOMAIN', 'xauterminal.com')}")
EMAIL_CONFIRMATION_EXPIRES_HOURS = int(os.getenv("EMAIL_CONFIRMATION_EXPIRES_HOURS", "24"))
EMAIL_CONFIRMATION_REQUIRED = os.getenv("EMAIL_CONFIRMATION_REQUIRED", "true").lower() in {"1", "true", "yes"}

RATE_LIMIT_WINDOW_SECONDS = 15 * 60
AUTH_RATE_LIMIT_MAX = 8
