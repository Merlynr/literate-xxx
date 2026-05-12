from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.styles import router as styles_router
from app.api.v1.terms import router as terms_router
from app.api.v1.promo_rules import router as promo_rules_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(auth_router, tags=["auth"])
router.include_router(categories_router, tags=["categories"])
router.include_router(styles_router, tags=["styles"])
router.include_router(terms_router, tags=["terms"])
router.include_router(promo_rules_router, tags=["promo-rules"])
router.include_router(uploads_router, tags=["uploads"])
router.include_router(tasks_router, tags=["tasks"])
