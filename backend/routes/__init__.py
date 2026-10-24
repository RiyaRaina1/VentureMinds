from backend.routes.health import router as health_router
from backend.routes.startups import router as startups_router
from backend.routes.simulation import router as simulation_router
from backend.routes.chat import router as chat_router
from backend.routes.validation import router as validation_router

__all__ = [
    "health_router",
    "startups_router",
    "simulation_router",
    "chat_router",
    "validation_router",
]
