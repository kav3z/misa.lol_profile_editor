"""
Controller Layer: REST API Endpoints.

Handles:
- GET /api/profile -> Returns 200 with the active profile.
- PUT /api/profile -> Accepts, validates, and persists profile updates.
                      On failure, returns 400 and leaves database unchanged.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.models.profile import ProfilePayload, ProfileResponse, UserProfile

api_router = APIRouter(prefix="/api", tags=["Profile API"])


@api_router.get(
    "/profile",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current profile",
    description="Returns the current single user profile in the required contract shape."
)
def get_profile(session: Session = Depends(get_session)) -> dict:
    """
    Fetch the active profile record (id=1).
    If missing for any reason, raises a 404.
    """
    profile = session.get(UserProfile, 1)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found."
        )
    return profile.to_dict()


@api_router.put(
    "/profile",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update profile",
    description="Validates and updates the profile. In case of validation failure, leaves stored profile intact and returns 400."
)
def update_profile(
    payload: ProfilePayload,
    session: Session = Depends(get_session)
) -> dict:
    """
    Update the active profile record (id=1).
    Validation is handled by the ProfilePayload Pydantic schema before reaching here.
    If the payload is invalid, FastAPI's validation exception handler intercepts it,
    formats a clear error response, and returns status 400 without modifying the database.
    """
    profile = session.get(UserProfile, 1)
    if not profile:
        # If not present, create record 1
        profile = UserProfile(
            id=1,
            display_name=payload.displayName,
            bio=payload.bio,
            link_label=payload.link.label,
            link_url=payload.link.url,
        )
        session.add(profile)
    else:
        # Update existing record
        profile.display_name = payload.displayName
        profile.bio = payload.bio
        profile.link_label = payload.link.label
        profile.link_url = payload.link.url
        session.add(profile)

    session.commit()
    session.refresh(profile)

    return profile.to_dict()
