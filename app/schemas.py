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


class AccountProfilePayload(BaseModel):
    first_name: str = ""
    last_name: str = ""
    address_line: str = ""
    postal_code: str = ""
    city: str = ""
    country: str = ""


class AccountPasswordPayload(BaseModel):
    current_password: str
    new_password: str


class PreferencesPayload(BaseModel):
    prefs: dict[str, Any]


class AdminAccessPayload(BaseModel):
    action: str


class BillingCheckoutPayload(BaseModel):
    plan: str
    return_path: str = "/terminal"


class BillingCheckoutSyncPayload(BaseModel):
    session_id: str


class BillingPortalPayload(BaseModel):
    return_path: str = "/terminal"
