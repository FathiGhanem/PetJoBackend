from fastapi import APIRouter

from api.v1.endpoints import (
    admin,
    advertisements,
    auth,
    breeding,
    favorites,
    heroes,
    missing_animals,
    pet_help,
    pet_photos,
    pets,
    profiles,
    public,
    reports,
    upload,
    users,
)


api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(pets.router, prefix="/pets", tags=["pets"])
api_router.include_router(pet_photos.router, prefix="/pets", tags=["pet-photos"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["favorites"])
api_router.include_router(heroes.router, prefix="/heroes", tags=["heroes"])
api_router.include_router(pet_help.router, prefix="/pet-help", tags=["pet-help"])
api_router.include_router(breeding.router, prefix="/breeding", tags=["breeding"])
api_router.include_router(missing_animals.router, prefix="/missing-animals", tags=["missing-animals"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(advertisements.router, prefix="/advertisements", tags=["advertisements"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(public.router, prefix="/public", tags=["public"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
