#!/usr/bin/env python3
"""Test script to check email configuration"""

import os

def test_email_config():
    print("=== EMAIL CONFIGURATION TEST ===")

    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
    EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", f"noreply@{os.getenv('EMAIL_DOMAIN', 'xauterminal.com')}")
    EMAIL_CONFIRMATION_REQUIRED = os.getenv("EMAIL_CONFIRMATION_REQUIRED", "true").lower() in {"1", "true", "yes"}

    print(f"EMAIL_CONFIRMATION_REQUIRED: {EMAIL_CONFIRMATION_REQUIRED}")
    print(f"RESEND_API_KEY: '{'***' if RESEND_API_KEY else ''}' (bool: {bool(RESEND_API_KEY)})")
    print(f"EMAIL_FROM_ADDRESS: '{EMAIL_FROM_ADDRESS}' (bool: {bool(EMAIL_FROM_ADDRESS)})")

    is_enabled = EMAIL_CONFIRMATION_REQUIRED and bool(RESEND_API_KEY and EMAIL_FROM_ADDRESS)
    print(f"is_email_confirmation_enabled(): {is_enabled}")

    if not RESEND_API_KEY:
        print("RESEND_API_KEY is empty.")
    if not EMAIL_FROM_ADDRESS:
        print("EMAIL_FROM_ADDRESS is empty.")

    if is_enabled:
        print("Email configuration looks good")
    else:
        print("Email configuration is incomplete")

if __name__ == "__main__":
    test_email_config()
