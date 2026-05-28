"""Schemas cho quản lý phiên/thiết bị."""
from datetime import datetime

from pydantic import BaseModel


class SessionOut(BaseModel):
    session_id: str
    device_name: str
    user_agent: str
    ip_address: str
    created_at: datetime
    last_active: datetime
    is_current: bool = False

    model_config = {"from_attributes": True}


class RevokedCountOut(BaseModel):
    message: str
    revoked: int
