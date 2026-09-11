"""FastUI Notifications Domain Schemas & DTOs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PushSubscriptionKeys(BaseModel):
    p256dh: str = Field(..., description="P256DH public key from browser PushManager")
    auth: str = Field(..., description="Authentication secret from browser PushManager")


class PushSubscriptionCreate(BaseModel):
    endpoint: str = Field(..., description="Unique push service subscription endpoint URL")
    keys: PushSubscriptionKeys
    user_agent: str | None = Field(None, description="Optional browser user-agent string")


class PushSubscriptionResponse(BaseModel):
    id: int
    endpoint: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VapidPublicKeyResponse(BaseModel):
    public_key: str


class TestNotificationRequest(BaseModel):
    title: str | None = "FastUI Reminder"
    body: str | None = "This is a test notification from FastUI."
    url: str | None = "/prospects"


class BroadcastNotificationRequest(BaseModel):
    user_id: int | None = Field(
        None, description="Optional target user ID (defaults to authenticated user)"
    )
    all_accounts: bool = Field(
        False, description="If true, broadcasts to all registered accounts and devices"
    )
    title: str = Field(..., min_length=1, max_length=200, description="Notification title")
    body: str = Field(..., min_length=1, max_length=500, description="Notification body content")
    url: str | None = Field(
        "/prospects", description="Target destination URL on notification click"
    )
    business_id: int | None = Field(None, description="Optional associated business ID")
    tag: str | None = Field(None, description="Optional notification deduplication tag")


class BroadcastNotificationResponse(BaseModel):
    status: str = Field(..., description="Dispatch outcome status (sent or no_subscriptions)")
    user_id: int | None = Field(None, description="Intended target user ID (None if all accounts)")
    total_accounts: int | None = Field(None, description="Number of accounts reached")
    total_subscriptions: int = Field(
        ..., description="Total subscriptions found before deduplication"
    )
    unique_devices: int = Field(..., description="Unique active devices targeted")
    dispatched_devices: int = Field(..., description="Devices successfully notified")
    failed_devices: int = Field(..., description="Devices where delivery failed")
    cleaned_up_devices: int = Field(..., description="Stale or expired subscriptions purged")
