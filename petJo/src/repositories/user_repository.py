from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from models.user import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model (auth)."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google sub/ID."""
        result = await self.db.execute(
            select(User).where(User.google_id == google_id)
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        result = await self.db.execute(
            select(User.id).where(User.email == email)
        )
        user_id = result.scalar_one_or_none()
        return user_id is not None
    
    async def activate_user(self, user_id: UUID) -> Optional[User]:
        """Activate a user account."""
        user = await self.get_by_id(user_id)
        if user:
            user.is_active = True
            await self.db.commit()
            await self.db.refresh(user)
        return user
    
    async def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """Deactivate a user account."""
        user = await self.get_by_id(user_id)
        if user:
            user.is_active = False
            await self.db.commit()
            await self.db.refresh(user)
        return user
