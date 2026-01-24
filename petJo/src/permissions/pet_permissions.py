"""Permission checking utilities."""

from typing import Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.user import User
from models.pet import Pet
from core.security import get_current_user_id
from exceptions import PermissionDeniedException, NotFoundException


async def check_is_admin(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Check if current user is an admin."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(User).where(User.id == UUID(current_user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundException("User")
    
    if not user.is_superuser:
        raise PermissionDeniedException("access admin resources")
    
    return user


async def check_pet_owner(
    pet_id: UUID,
    current_user_id: str,
    db: AsyncSession
) -> bool:
    """Check if user owns the pet."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Pet).where(Pet.id == pet_id)
    )
    pet = result.scalar_one_or_none()
    
    if not pet:
        return False
    
    return str(pet.owner_id) == str(current_user_id)


async def require_pet_owner(
    pet_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> Pet:
    """Require user to be the pet owner."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Pet).where(Pet.id == pet_id)
    )
    pet = result.scalar_one_or_none()
    
    if not pet:
        raise NotFoundException("Pet")
    
    if str(pet.owner_id) != str(current_user_id):
        raise PermissionDeniedException("access this pet")
    
    return pet


async def can_modify_pet(
    pet_id: int,
    current_user_id: str,
    db: AsyncSession
) -> bool:
    """Check if user can modify the pet (owner or admin)."""
    from sqlalchemy import select
    
    # Check if user is admin
    result = await db.execute(
        select(Profile).where(Profile.id == UUID(current_user_id))
    )
    profile = result.scalar_one_or_none()
    
    if profile and profile.role == ROLE_ADMIN:
        return True
    
    # Check if user owns the pet
    return await check_pet_owner(pet_id, current_user_id, db)
