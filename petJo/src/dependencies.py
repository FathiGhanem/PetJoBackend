"""FastAPI dependency injection providers."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_current_user_id
from db.session import get_db
from exceptions import InactiveAccountException, SuperAdminRequiredException, UserNotFoundException
from models.user import User
from repositories.favorite_repository import FavoriteRepository
from repositories.hero_repository import HeroRepository
from repositories.pet_help_repository import PetHelpRequestRepository
from repositories.pet_photo_repository import PetPhotoRepository
from repositories.pet_repository import PetRepository
from repositories.report_repository import ReportRepository
from repositories.user_repository import UserRepository
from repositories.breeding_request_repository import BreedingRequestRepository
from repositories.missing_animal_repository import MissingAnimalRepository
from services.favorite_service import FavoriteService
from services.hero_service import HeroService
from services.pet_help_service import PetHelpRequestService
from services.pet_photo_service import PetPhotoService
from services.pet_service import PetService
from services.report_service import ReportService
from services.user_service import UserService
from services.breeding_request_service import BreedingRequestService
from services.missing_animal_service import MissingAnimalService

logger = logging.getLogger(__name__)


# ==================== Repository Dependencies ====================

def get_favorite_repository(db: AsyncSession = Depends(get_db)) -> FavoriteRepository:
    """Get favorite repository."""
    return FavoriteRepository(db)


def get_hero_repository(db: AsyncSession = Depends(get_db)) -> HeroRepository:
    """Get hero repository."""
    return HeroRepository(db)


def get_pet_repository(db: AsyncSession = Depends(get_db)) -> PetRepository:
    """Get pet repository."""
    return PetRepository(db)


def get_pet_help_repository(db: AsyncSession = Depends(get_db)) -> PetHelpRequestRepository:
    """Get pet help request repository."""
    return PetHelpRequestRepository(db)


def get_pet_photo_repository(db: AsyncSession = Depends(get_db)) -> PetPhotoRepository:
    """Get pet photo repository."""
    return PetPhotoRepository(db)


def get_report_repository(db: AsyncSession = Depends(get_db)) -> ReportRepository:
    """Get report repository."""
    return ReportRepository(db)


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Get user repository."""
    return UserRepository(db)


def get_breeding_request_repository(db: AsyncSession = Depends(get_db)) -> BreedingRequestRepository:
    """Get breeding request repository."""
    return BreedingRequestRepository(db)


def get_missing_animal_repository(db: AsyncSession = Depends(get_db)) -> MissingAnimalRepository:
    """Get missing animal repository."""
    return MissingAnimalRepository(db)


# ==================== Service Dependencies ====================

def get_favorite_service(
    repository: FavoriteRepository = Depends(get_favorite_repository)
) -> FavoriteService:
    """Get favorite service."""
    return FavoriteService(repository)


def get_hero_service(
    repository: HeroRepository = Depends(get_hero_repository)
) -> HeroService:
    """Get hero service."""
    return HeroService(repository)


def get_pet_service(
    repository: PetRepository = Depends(get_pet_repository)
) -> PetService:
    """Get pet service."""
    return PetService(repository)


def get_pet_help_service(
    repository: PetHelpRequestRepository = Depends(get_pet_help_repository)
) -> PetHelpRequestService:
    """Get pet help request service."""
    return PetHelpRequestService(repository)


def get_pet_photo_service(
    repository: PetPhotoRepository = Depends(get_pet_photo_repository)
) -> PetPhotoService:
    """Get pet photo service."""
    return PetPhotoService(repository)


def get_report_service(
    repository: ReportRepository = Depends(get_report_repository)
) -> ReportService:
    """Get report service."""
    return ReportService(repository)


def get_user_service(
    repository: UserRepository = Depends(get_user_repository)
) -> UserService:
    """Get user service."""
    return UserService(repository)


def get_breeding_request_service(
    repository: BreedingRequestRepository = Depends(get_breeding_request_repository)
) -> BreedingRequestService:
    """Get breeding request service."""
    return BreedingRequestService(repository)


def get_missing_animal_service(
    repository: MissingAnimalRepository = Depends(get_missing_animal_repository)
) -> MissingAnimalService:
    """Get missing animal service."""
    return MissingAnimalService(repository)


# ==================== User Authentication Dependencies ====================

async def get_current_user(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    result = await db.execute(
        select(User).where(User.id == UUID(current_user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise UserNotFoundException()
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise InactiveAccountException()
    
    return current_user


async def get_optional_current_user(
    current_user_id: Optional[str] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not current_user_id:
        return None
    
    try:
        result = await db.execute(
            select(User).where(User.id == UUID(current_user_id))
        )
        return result.scalar_one_or_none()
    except Exception:
        return None


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current superuser (admin only).
    
    Raises:
        SuperAdminRequiredException: If user is not a superuser.
    """
    if not current_user.is_superuser:
        raise SuperAdminRequiredException()
    
    return current_user
