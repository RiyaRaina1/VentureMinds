import os
import sys
from pathlib import Path

# Add backend directory and its parent to sys.path for universal import compatibility
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
for p in [str(current_dir), str(parent_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Load environment configuration
env_path = current_dir / ".env"
load_dotenv(dotenv_path=env_path)

from backend.database.connection import init_db
from backend.routes.health import router as health_router
from backend.routes.startups import router as startups_router
from backend.routes.simulation import router as simulation_router
from backend.routes.chat import router as chat_router
from backend.routes.validation import router as validation_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events."""
    # Initialize database tables on application start
    init_db()
    yield


app = FastAPI(
    title="VentureMind AI API",
    description="Backend foundation, deterministic financial simulation engine, and Real AI Chat Studio for VentureMind AI (Phase 2).",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS for local frontend development
frontend_env_url = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")
allowed_origins = list({
    frontend_env_url,
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://localhost:3000"
})

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Global Exception Handlers (Clean JSON, no stack traces leaked)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "code": exc.status_code, "detail": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        errors.append(f"{field}: {msg}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "code": 422,
            "detail": "Validation error",
            "errors": errors
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "code": 500,
            "detail": "Internal server error. Please verify input parameters or contact administrator."
        }
    )


# Include Feature Routers
app.include_router(health_router)
app.include_router(startups_router)
app.include_router(simulation_router)
app.include_router(chat_router)
app.include_router(validation_router)


@app.get("/", tags=["Root"])
def root_entry():
    """Root entrypoint linking to interactive documentation."""
    return {
        "message": "VentureMind AI API Foundation (Phase 2)",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
