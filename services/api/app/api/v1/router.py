"""FastUI API v1 Router Aggregator.

Consolidates all domain sub-routers under the /v1 prefix.
"""

from fastapi import APIRouter

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.businesses import router as businesses_router
from app.api.v1.routes.demos import router as demos_router
from app.api.v1.routes.engagement import router as engagement_router
from app.api.v1.routes.enrichment import router as enrichment_router
from app.api.v1.routes.exports import router as exports_router
from app.api.v1.routes.leads import router as leads_router
from app.api.v1.routes.notifications import router as notifications_router
from app.api.v1.routes.pipeline import router as pipeline_router
from app.api.v1.routes.prospecting import router as prospecting_router
from app.api.v1.routes.prospects import router as prospects_router
from app.api.v1.routes.stats import router as stats_router

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(auth_router)
v1_router.include_router(businesses_router)
v1_router.include_router(prospects_router)
v1_router.include_router(leads_router)
v1_router.include_router(pipeline_router)
v1_router.include_router(engagement_router)
v1_router.include_router(demos_router)
v1_router.include_router(enrichment_router)
v1_router.include_router(prospecting_router)
v1_router.include_router(exports_router)
v1_router.include_router(notifications_router)
v1_router.include_router(stats_router)
