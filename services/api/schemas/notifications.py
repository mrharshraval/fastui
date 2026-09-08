from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PushSubscriptionKeys(BaseModel):
    p256dh: str = Field(..., description="P256DH public key from browser PushManager")
    auth: str = Field(..., description="Authentication secret from browser PushManager")


class PushSubscriptionCreate(BaseModel):
    endpoint: str = Field(..., description="Unique push service subscription endpoint URL")
    keys: PushSubscriptionKeys
    user_agent: Optional[str] = Field(None, description="Optional browser user-agent string")


class PushSubscriptionResponse(BaseModel):
    id: int
    endpoint: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class VapidPublicKeyResponse(BaseModel):
    public_key: str


class TestNotificationRequest(BaseModel):
    title: Optional[str] = "FastUI Reminder"
    body: Optional[str] = "This is a test notification from FastUI."
    url: Optional[str] = "/prospects"


class BroadcastNotificationRequest(BaseModel):
    user_id: Optional[int] = Field(None, description="Optional target user ID (defaults to authenticated user)")
    all_accounts: bool = Field(False, description="If true, broadcasts to all registered accounts and devices")
    title: str = Field(..., min_length=1, max_length=200, description="Notification title")
    body: str = Field(..., min_length=1, max_length=500, description="Notification body content")
    url: Optional[str] = Field("/prospects", description="Target destination URL on notification click")
    business_id: Optional[int] = Field(None, description="Optional associated business ID")
    tag: Optional[str] = Field(None, description="Optional notification deduplication tag")


class BroadcastNotificationResponse(BaseModel):
    status: str = Field(..., description="Dispatch outcome status (sent or no_subscriptions)")
    user_id: Optional[int] = Field(None, description="Intended target user ID (None if all accounts)")
    total_accounts: Optional[int] = Field(None, description="Number of accounts reached")
    total_subscriptions: int = Field(..., description="Total subscriptions found before deduplication")
    unique_devices: int = Field(..., description="Unique active devices targeted")
    dispatched_devices: int = Field(..., description="Devices successfully notified")
    failed_devices: int = Field(..., description="Devices where delivery failed")
    cleaned_up_devices: int = Field(..., description="Stale or expired subscriptions purged")

