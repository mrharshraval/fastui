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
