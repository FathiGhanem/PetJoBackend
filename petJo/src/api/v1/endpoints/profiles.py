"""User profile endpoints."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import get_current_user_id, get_password_hash
from core.storage import get_storage_service
from db.session import get_db
from models.user import User as UserModel
from schemas.common import ApiResponse
from schemas.user import Profile, ProfileUpdate, ProfilePublic

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/me",
    response_model=ApiResponse[Profile],
    summary="Get current user profile",
)
async def get_my_profile(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated user's profile."""
    result = await db.execute(
        select(UserModel).where(UserModel.id == UUID(current_user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return ApiResponse(
        success=True,
        data=user,
        message="Profile retrieved successfully",
    )


@router.patch(
    "/me",
    response_model=ApiResponse[Profile],
    summary="Update current user profile",
)
async def update_my_profile(
    profile_update: ProfileUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile fields."""
    result = await db.execute(
        select(UserModel).where(UserModel.id == UUID(current_user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return ApiResponse(
        success=True,
        data=user,
        message="Profile updated successfully",
    )


@router.post(
    "/me/avatar",
    response_model=ApiResponse[dict],
    summary="Upload profile avatar",
)
async def upload_avatar(
    file: UploadFile = File(..., description="Avatar image file"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload and set the user's avatar image."""
    result = await db.execute(
        select(UserModel).where(UserModel.id == UUID(current_user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Validate file type
    allowed_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed: JPEG, PNG, WebP",
        )

    storage = get_storage_service()
    try:
        url = await storage.upload_file(
            file=file.file,
            filename=file.filename,
            content_type=file.content_type,
            folder="avatars",
        )
    except Exception as e:
        logger.error(f"Avatar upload failed for user {current_user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar",
        )

    user.avatar_url = url
    await db.commit()
    await db.refresh(user)

    return ApiResponse(
        success=True,
        data={"url": url},
        message="Avatar uploaded successfully",
    )


@router.patch(
    "/me/email",
    response_model=ApiResponse[Profile],
    summary="Update profile email",
)
async def update_email(
    payload: dict,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update the user's email address."""
    new_email = payload.get("email")
    if not new_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required",
        )

    # Check uniqueness
    existing = await db.execute(
        select(UserModel).where(
            UserModel.email == new_email,
            UserModel.id != UUID(current_user_id),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use",
        )

    result = await db.execute(
        select(UserModel).where(UserModel.id == UUID(current_user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.email = new_email
    await db.commit()
    await db.refresh(user)

    return ApiResponse(
        success=True,
        data=user,
        message="Email updated successfully",
    )


@router.patch(
    "/me/password",
    response_model=ApiResponse[dict],
    summary="Update profile password",
)
async def update_password(
    payload: dict,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update the user's password."""
    new_password = payload.get("new_password")
    if not new_password or len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    result = await db.execute(
        select(UserModel).where(UserModel.id == UUID(current_user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.hashed_password = get_password_hash(new_password)
    await db.commit()

    return ApiResponse(
        success=True,
        data={"message": "Password updated successfully"},
        message="Password updated successfully",
    )


@router.get(
    "/{user_id}",
    response_model=ApiResponse[ProfilePublic],
    summary="Get user profile by ID",
)
async def get_profile_by_id(
    user_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a user's public profile by their ID."""
    result = await db.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return ApiResponse(
        success=True,
        data=user,
        message="Profile retrieved successfully",
    )
