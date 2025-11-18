# app/routes/users.py
from fastapi import APIRouter, Depends

from ..schemas.users import MeResponse, UserProfile
from ..dependencies.users import get_current_active_user

router = APIRouter()


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current authenticated user profile",
    description="Returns the profile stored in public.usuarios for the current user.",
    tags=["users"],
)
async def read_me(current_user: UserProfile = Depends(get_current_active_user)):
    return MeResponse(user=current_user)
