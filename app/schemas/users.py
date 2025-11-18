# app/schemas/users.py
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class UserProfile(BaseModel):
    id: UUID
    email: EmailStr
    username: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None

    role: Literal["usuario", "owner", "admin"]

    level_numeric: int = Field(..., alias="nivel_gamificacion")
    gamification_level: str
    points_balance: int = Field(..., alias="puntos")
    points_lifetime: int
    points_spent: int
    badges: List[str] = Field(default_factory=list)

    membership_plan: str
    membership_status: str
    membership_started_at: Optional[datetime] = None
    membership_expires_at: Optional[datetime] = None

    is_blocked: bool = Field(..., alias="bloqueado")
    blocked_at: Optional[datetime] = None
    blocked_reason: Optional[str] = None

    last_session_at: Optional[datetime] = Field(default=None, alias="ultima_sesion")
    created_at: datetime

    preferences: Dict[str, Any] = Field(default_factory=dict)
    referral_code: Optional[str] = None
    referred_by_user_id: Optional[UUID] = None
    referrals_count: int

    class Config:
        orm_mode = True


class MeResponse(BaseModel):
    user: UserProfile
