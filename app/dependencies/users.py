# app/dependencies/users.py
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status

from ..db import get_pool
from ..schemas.users import UserProfile


@dataclass
class CurrentUserAuth:
  id: UUID
  email: str


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
) -> CurrentUserAuth:
  """
  Extracts the Supabase JWT from Authorization header and returns basic auth info.

  TODO: Validate the JWT against Supabase. For now, expects a Bearer token in the
  format "Bearer <user_id>|<email>" during local development.
  """
  if not authorization or not authorization.lower().startswith("bearer "):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Missing or invalid authorization header",
    )

  token = authorization.split(" ", 1)[1].strip()

  # Attempt to derive user_id and email from a simple dev format.
  user_id: Optional[UUID] = None
  email: Optional[str] = None
  if "|" in token:
    possible_id, possible_email = token.split("|", 1)
    try:
      user_id = UUID(possible_id)
      email = possible_email
    except ValueError:
      user_id = None

  if user_id is None:
    # Production: replace this with real Supabase JWT validation and claims extraction
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Unable to decode user from token (TODO: Supabase JWT validation)",
    )

  return CurrentUserAuth(id=user_id, email=email or "")


async def get_current_active_user(
    current: CurrentUserAuth = Depends(get_current_user),
) -> UserProfile:
  """
  Fetches the active user profile from public.usuarios using the auth info.
  """
  sql = """
  SELECT
    u.id,
    u.email,
    u.username,
    u.avatar_url,
    u.rol,
    u.nivel_gamificacion,
    u.puntos,
    u.bloqueado,
    u.ultima_sesion,
    u.created_at,
    u.blocked_at,
    u.blocked_reason,
    u.preferences,
    u.gamification_level,
    u.points_lifetime,
    u.points_spent,
    u.badges,
    u.membership_plan,
    u.membership_status,
    u.membership_started_at,
    u.membership_expires_at,
    u.referral_code,
    u.referred_by_user_id,
    u.referrals_count
  FROM public.usuarios AS u
  WHERE u.id = $1;
  """

  pool = await get_pool()
  async with pool.acquire() as conn:
    row = await conn.fetchrow(sql, current.id)

  if row is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")

  if row["bloqueado"]:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is blocked")

  preferences = row["preferences"] or {}
  badges = row["badges"] or []

  return UserProfile(
    id=row["id"],
    email=row["email"],
    username=row["username"],
    avatar_url=row["avatar_url"],
    role=row["rol"],
    level_numeric=row["nivel_gamificacion"],
    gamification_level=row["gamification_level"],
    points_balance=row["puntos"],
    points_lifetime=row["points_lifetime"],
    points_spent=row["points_spent"],
    badges=badges,
    membership_plan=row["membership_plan"],
    membership_status=row["membership_status"],
    membership_started_at=row["membership_started_at"],
    membership_expires_at=row["membership_expires_at"],
    is_blocked=row["bloqueado"],
    blocked_at=row["blocked_at"],
    blocked_reason=row["blocked_reason"],
    last_session_at=row["ultima_sesion"],
    created_at=row["created_at"],
    preferences=preferences,
    referral_code=row["referral_code"],
    referred_by_user_id=row["referred_by_user_id"],
    referrals_count=row["referrals_count"],
  )


__all__ = ["CurrentUserAuth", "get_current_user", "get_current_active_user"]
