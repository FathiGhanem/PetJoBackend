"""Script to seed initial pet categories in the database."""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from db.base import Base  # Import all models
from db.session import AsyncSessionLocal
from models.category import Category

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_categories():
    """
    Seed the database with initial pet categories.
    
    Creates categories if they don't already exist.
    Categories include: Dogs, Cats, Birds, Fish, Rabbits, Hamsters, Reptiles, Other.
    """
    categories_data = [
        {"name": "Dogs", "image_url": None},
        {"name": "Cats", "image_url": None},
        {"name": "Birds", "image_url": None},
        {"name": "Fish", "image_url": None},
        {"name": "Rabbits", "image_url": None},
        {"name": "Hamsters", "image_url": None},
        {"name": "Reptiles", "image_url": None},
        {"name": "Other", "image_url": None},
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if categories already exist
            result = await db.execute(select(Category))
            existing = result.scalars().all()
            
            if existing:
                logger.info(f"Categories already exist ({len(existing)} found)")
                for cat in existing:
                    logger.info(f"  - {cat.id}: {cat.name}")
                return
            
            # Create categories
            for cat_data in categories_data:
                category = Category(**cat_data)
                db.add(category)
            
            await db.commit()
            
            # Fetch created categories
            result = await db.execute(select(Category))
            categories = result.scalars().all()
            
            logger.info(f"✓ Created {len(categories)} categories:")
            for cat in categories:
                logger.info(f"  - {cat.id}: {cat.name}")
            
        except Exception as e:
            logger.error(f"Error seeding categories: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_categories())
