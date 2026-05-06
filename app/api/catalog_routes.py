"""
app/api/catalog_routes — Zanovix services catalog endpoint.

Routes:
  GET /api/catalog/services — unauthenticated (ADR-15); returns full catalog

The catalog is loaded once at module import from app/config/zanovix_services.yaml.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.synthesis.catalog import ServiceDef, get_catalog

router = APIRouter(tags=["catalog"])


class CatalogResponse(BaseModel):
    services: list[ServiceDef]


@router.get("/catalog/services", response_model=CatalogResponse)
async def get_services_catalog() -> CatalogResponse:
    """
    Returns the full Zanovix services catalog.

    Unauthenticated endpoint (ADR-15) — catalog content is not sensitive
    and the frontend needs it before any auth flow.
    """
    return CatalogResponse(services=get_catalog())
