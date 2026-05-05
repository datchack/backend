#!/usr/bin/env python3
"""Test script to check email configuration"""

import os

def test_email_config():
    print("=== EMAIL CONFIGURATION TEST ===")

    EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "")
    EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587")) if os.getenv("EMAIL_SMTP_PORT") else 0
    EMAIL_SMTP_USER = os.getenv("EMAIL_SMTP_USER", "")
    EMAIL_SMTP_PASSWORD = os.getenv("EMAIL_SMTP_PASSWORD", "")
    EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", f"noreply@{os.getenv('EMAIL_DOMAIN', 'xauterminal.com')}")
    EMAIL_CONFIRMATION_REQUIRED = os.getenv("EMAIL_CONFIRMATION_REQUIRED", "true").lower() in {"1", "true", "yes"}

    print(f"EMAIL_CONFIRMATION_REQUIRED: {EMAIL_CONFIRMATION_REQUIRED}")
    print(f"EMAIL_SMTP_HOST: '{EMAIL_SMTP_HOST}' (bool: {bool(EMAIL_SMTP_HOST)})")
    print(f"EMAIL_SMTP_PORT: {EMAIL_SMTP_PORT}")
    print(f"EMAIL_SMTP_USER: '{EMAIL_SMTP_USER}' (bool: {bool(EMAIL_SMTP_USER)})")
    print(f"EMAIL_SMTP_PASSWORD: '{'***' if EMAIL_SMTP_PASSWORD else ''}' (bool: {bool(EMAIL_SMTP_PASSWORD)})")
    print(f"EMAIL_FROM_ADDRESS: '{EMAIL_FROM_ADDRESS}' (bool: {bool(EMAIL_FROM_ADDRESS)})")

    is_enabled = EMAIL_CONFIRMATION_REQUIRED and bool(EMAIL_SMTP_HOST and EMAIL_SMTP_PORT and EMAIL_FROM_ADDRESS)
    print(f"is_email_confirmation_enabled(): {is_enabled}")

    if not EMAIL_SMTP_HOST:
        print("❌ EMAIL_SMTP_HOST is empty!")
    if not EMAIL_SMTP_PORT:
        print("❌ EMAIL_SMTP_PORT is 0!")
    if not EMAIL_FROM_ADDRESS:
        print("❌ EMAIL_FROM_ADDRESS is empty!")

    if is_enabled:
        print("✅ Email configuration looks good")
    else:
        print("❌ Email configuration is incomplete")

if __name__ == "__main__":
    test_email_config()