from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from pydantic import BaseModel, Field

from db.session import get_db
from models.user import User as UserModel
from schemas.user import User, UserUpdate, UserPublic
from schemas.common import ApiResponse
from core.security import get_current_user_id
from dependencies import get_user_service
from services.user_service import UserService


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


router = APIRouter()


@router.get("/me", response_model=ApiResponse[User])
async def get_current_user(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile."""
    result = await db.execute(select(UserModel).where(UserModel.id == UUID(current_user_id)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return ApiResponse(
        success=True,
        data=user,
        message="User profile retrieved successfully"
    )


@router.patch("/me", response_model=ApiResponse[User])
async def update_current_user(
    user_update: UserUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile."""
    result = await db.execute(select(UserModel).where(UserModel.id == UUID(current_user_id)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_data = user_update.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        from core.security import get_password_hash
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return ApiResponse(
        success=True,
        data=user,
        message="User profile updated successfully"
    )


@router.post("/me/change-password", response_model=ApiResponse[dict])
async def change_password(
    password_data: ChangePasswordRequest,
    current_user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    """Change current user's password."""
    success = await user_service.change_password(
        user_id=UUID(current_user_id),
        old_password=password_data.old_password,
        new_password=password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid old password"
        )
    
    return ApiResponse(
        success=True,
        data={"message": "Password changed successfully"},
        message="Password changed successfully"
    )


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Get user by ID."""
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user
