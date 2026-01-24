"""Script to create or update the initial superuser account."""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import settings
from db.base import Base  # Import all models
from db.session import AsyncSessionLocal
from repositories.user_repository import UserRepository
from services.user_service import UserService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_initial_superuser():
    """
    Create the initial superuser if it doesn't exist.
    
    If the user already exists, updates them to superuser status.
    Credentials are read from environment settings.
    """
    async with AsyncSessionLocal() as db:
        try:
            user_repository = UserRepository(db)
            user_service = UserService(user_repository)
            
            # Check if superuser already exists
            existing_user = await user_repository.get_by_email(
                settings.FIRST_SUPERUSER_EMAIL
            )
            
            if existing_user:
                logger.info(f"Superuser already exists: {settings.FIRST_SUPERUSER_EMAIL}")
                if not existing_user.is_superuser:
                    # Update to superuser if exists but not superuser
                    await user_repository.update(
                        existing_user.id,
                        {"is_superuser": True}
                    )
                    await db.commit()
                    logger.info(f"Updated user to superuser: {settings.FIRST_SUPERUSER_EMAIL}")
                return
            
            # Create superuser
            superuser = await user_service.create_superuser(
                email=settings.FIRST_SUPERUSER_EMAIL,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                full_name="Super Admin"
            )
            
            await db.commit()
            logger.info(f"✓ Superuser created successfully: {superuser.email}")
            logger.info(f"  Email: {settings.FIRST_SUPERUSER_EMAIL}")
            logger.info(f"  Password: {'*' * len(settings.FIRST_SUPERUSER_PASSWORD)}")
            logger.warning("⚠ Remember to change the default password!")
            
        except Exception as e:
            logger.error(f"Error creating superuser: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(create_initial_superuser())
