from db.base_class import Base

# Import all models here to ensure they are registered with Base
# This is important for Alembic migrations
from models.user import User  # noqa
from models.pet import Pet  # noqa
from models.category import Category  # noqa
from models.city import City  # noqa
from models.advertisement import Advertisement  # noqa
from models.favorite import Favorite  # noqa
from models.hero import Hero  # noqa
from models.pet_help_request import PetHelpRequest  # noqa
from models.pet_photo import PetPhoto  # noqa
from models.push_token import PushToken  # noqa
from models.report import Report  # noqa
from models.breeding_request import BreedingRequest  # noqa
from models.missing_animal import MissingAnimal  # noqa
