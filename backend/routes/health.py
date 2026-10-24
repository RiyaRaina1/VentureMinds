from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["System Health"])


@router.get("/health", summary="System Health Check")
def get_health():
    """Returns the operational status, service identifier, and version of VentureMind API."""
    return {
        "status": "ok",
        "service": "VentureMind API",
        "version": "1.0.0"
    }
