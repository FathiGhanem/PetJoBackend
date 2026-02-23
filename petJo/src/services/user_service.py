from typing import Optional
from uuid import UUID

from repositories.user_repository import UserRepository
from services.base import BaseService
from core.security import verify_password, get_password_hash
from core.config import settings


class UserService(BaseService[None, UserRepository]):
    """Service for User authentication logic."""
    
    async def authenticate(self, email: str, password: str):
        """Authenticate user by email and password."""
        user = await self.repository.get_by_email(email)
        
        if not user:
            return None
        
        # OAuth-only accounts have no password
        if not user.hashed_password:
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
    
    async def google_login_or_register(self, id_token: str):
        """Verify a Google ID token and return (or create) the matching user."""
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
        from exceptions import AuthenticationException

        if not settings.GOOGLE_CLIENT_ID:
            raise AuthenticationException("Google login is not configured")

        try:
            id_info = google_id_token.verify_oauth2_token(
                id_token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as exc:
            raise AuthenticationException(f"Invalid Google token: {exc}")

        google_sub: str = id_info["sub"]
        email: str = id_info.get("email", "")
        full_name: str = id_info.get("name", "")
        avatar_url: str = id_info.get("picture", "")

        # 1. Try to find user by google_id
        user = await self.repository.get_by_google_id(google_sub)
        if user:
            return user

        # 2. Try to find existing account by email and link it
        user = await self.repository.get_by_email(email)
        if user:
            await self.repository.update(user.id, {"google_id": google_sub})
            return user

        # 3. Create a brand-new user (no password — OAuth only)
        user_data = {
            "email": email,
            "hashed_password": None,
            "google_id": google_sub,
            "full_name": full_name or None,
            "avatar_url": avatar_url or None,
            "is_active": True,
            "is_superuser": False,
        }
        return await self.repository.create(user_data)

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
