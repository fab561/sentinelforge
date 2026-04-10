from fastapi import APIRouter

from app.api.alerts import router as alerts_router
from app.api.cases import router as cases_router
from app.api.rules import router as rules_router
from app.api.stats import router as stats_router
from app.api.wazuh import router as wazuh_router

api_router = APIRouter(prefix="/api")

api_router.include_router(alerts_router)
api_router.include_router(cases_router)
api_router.include_router(rules_router)
api_router.include_router(stats_router)
api_router.include_router(wazuh_router)
