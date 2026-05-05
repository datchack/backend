from typing import Any

from pydantic import BaseModel


class AccountAuthPayload(BaseModel):
    email: str
    password: str


class AccountConfirmEmailPayload(BaseModel):
    email: str
    code: str


class AccountResendConfirmationPayload(BaseModel):
    email: str


class PreferencesPayload(BaseModel):
    prefs: dict[str, Any]


class AdminAccessPayload(BaseModel):
    action: str


class BillingCheckoutPayload(BaseModel):
    plan: str
