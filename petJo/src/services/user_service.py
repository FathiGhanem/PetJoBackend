from typing import Optional
from uuid import UUID

from repositories.user_repository import UserRepository
from services.base import BaseService
from core.security import verify_password, get_password_hash


class UserService(BaseService[None, UserRepository]):
    """Service for User authentication logic."""
    
    async def authenticate(self, email: str, password: str):
        """Authenticate user by email and password."""
        user = await self.repository.get_by_email(email)
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    async def create_user(self, email: str, password: str, full_name: Optional[str] = None):
        """Create a new user with hashed password."""
        from exceptions import EmailAlreadyExistsException
        
        if await self.repository.email_exists(email):
            raise EmailAlreadyExistsException()
        
        user_data = {
            "email": email,
            "hashed_password": get_password_hash(password),
            "full_name": full_name,
            "is_active": True,
            "is_superuser": False
        }
        
        return await self.repository.create(user_data)
    
    async def change_password(self, user_id: UUID, old_password: str, new_password: str) -> bool:
        """Change user password."""
        user = await self.repository.get_by_id(user_id)
        
        if not user or not verify_password(old_password, user.hashed_password):
            return False
        
        await self.repository.update(
            user_id, 
            {"hashed_password": get_password_hash(new_password)}
        )
        return True
    
    async def activate_user(self, user_id: UUID):
        """Activate a user account."""
        return await self.repository.activate_user(user_id)
    
    async def deactivate_user(self, user_id: UUID):
        """Deactivate a user account."""
        return await self.repository.deactivate_user(user_id)
    
    async def create_superuser(self, email: str, password: str, full_name: Optional[str] = None):
        """Create a superuser account. Use only for initial setup."""
        from exceptions import EmailAlreadyExistsException
        
        if await self.repository.email_exists(email):
            raise EmailAlreadyExistsException()
        
        user_data = {
            "email": email,
            "hashed_password": get_password_hash(password),
            "full_name": full_name or "Super Admin",
            "is_active": True,
            "is_superuser": True
        }
        
        return await self.repository.create(user_data)
