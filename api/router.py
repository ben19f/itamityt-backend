from fastapi import APIRouter

from . import health, public
from . import items, users
from . import auth

router = APIRouter()

router.include_router(health.router)
router.include_router(items.router)
router.include_router(auth.router)
router.include_router(public.router)  # <-- новый публичный API
router.include_router(users.router)
