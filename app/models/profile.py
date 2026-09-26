"""
Model Layer: Profile entity and data transfer objects (DTOs).

Defines:
1. UserProfile: SQLModel database table for persisting profile data.
2. LinkItem & ProfilePayload: Pydantic schemas validating API inputs strictly
   according to the trial contract:
   - All four values must be strings (rejecting type coercion like numbers/booleans).
   - Values trimmed before length and format checks.
   - Display name: 1-40 chars.
   - Bio: 0-160 chars.
   - Link label: 1-30 chars.
   - Link URL: valid absolute https:// URL with a hostname.
"""
from typing import Optional
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, StrictStr, field_validator
from sqlmodel import Field, SQLModel


# ============================================================================
# DATABASE MODEL (SQLModel)
# ============================================================================

class UserProfile(SQLModel, table=True):
    """
    SQLModel database entity representing the stored user profile.
    For this single-profile trial, id=1 represents the active profile record.
    """
    __tablename__ = "user_profiles"

    id: Optional[int] = Field(default=1, primary_key=True)
    display_name: str = Field(nullable=False, max_length=40)
    bio: str = Field(default="", nullable=False, max_length=160)
    link_label: str = Field(nullable=False, max_length=30)
    link_url: str = Field(nullable=False)

    def to_dict(self) -> dict:
        """Serializes the database model to the contract JSON format."""
        return {
            "displayName": self.display_name,
            "bio": self.bio,
            "link": {
                "label": self.link_label,
                "url": self.link_url
            }
        }


# ============================================================================
# DATA TRANSFER OBJECTS (Pydantic Schemas with Strict Validation)
# ============================================================================

class LinkItem(BaseModel):
    """
    Validates the nested 'link' object.
    Strictly requires strings and applies whitespace trimming + business rules.
    """
    model_config = ConfigDict(strict=True)

    label: StrictStr
    url: StrictStr

    @field_validator("label", mode="after")
    @classmethod
    def validate_label(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 1:
            raise ValueError("Link label cannot be empty (must be 1–30 characters after trimming).")
        if len(trimmed) > 30:
            raise ValueError(f"Link label is too long ({len(trimmed)} chars; maximum allowed is 30).")
        return trimmed

    @field_validator("url", mode="after")
    @classmethod
    def validate_url(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Link URL cannot be empty.")

        # Parse URL
        try:
            parsed = urlsplit(trimmed)
        except Exception:
            raise ValueError("Link URL is malformed.")

        # Enforce https scheme
        if parsed.scheme.lower() != "https":
            raise ValueError("Link URL must be an absolute URL starting with 'https://'. Other schemes (http, javascript, data) are rejected.")

        # Enforce hostname presence
        if not parsed.hostname or len(parsed.hostname.strip()) == 0:
            raise ValueError("Link URL must include a valid hostname.")

        # Disallow spaces or control characters in URL
        if any(c.isspace() for c in trimmed):
            raise ValueError("Link URL cannot contain spaces.")

        return trimmed


class ProfilePayload(BaseModel):
    """
    Validates incoming PUT /api/profile payload.
    StrictStr ensures numbers, booleans, or other non-string types fail validation.
    """
    model_config = ConfigDict(strict=True)

    displayName: StrictStr
    bio: StrictStr
    link: LinkItem

    @field_validator("displayName", mode="after")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 1:
            raise ValueError("Display name cannot be empty (must be 1–40 characters after trimming).")
        if len(trimmed) > 40:
            raise ValueError(f"Display name is too long ({len(trimmed)} chars; maximum allowed is 40).")
        return trimmed

    @field_validator("bio", mode="after")
    @classmethod
    def validate_bio(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) > 160:
            raise ValueError(f"Bio is too long ({len(trimmed)} chars; maximum allowed is 160).")
        return trimmed


class ProfileResponse(BaseModel):
    """
    Output model matching the JSON contract shape.
    """
    displayName: str
    bio: str
    link: LinkItem
