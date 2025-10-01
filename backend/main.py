from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api import projects, env_vars, exports, imports, variable_history, search

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting MD-Linked-Secrets API...")
    await init_db()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MD-Linked-Secrets API...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="A local secret management tool for managing and linking environment variables across multiple projects",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint for uptime monitoring"""
    return {
        "status": "healthy",
        "service": settings.project_name,
        "version": settings.version,
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with database connectivity"""
    from app.core.database import get_db
    from sqlalchemy import text
    import time
    
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "service": settings.project_name,
        "version": settings.version,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checks": {}
    }
    
    # Database connectivity check
    try:
        async for db in get_db():
            await db.execute(text("SELECT 1"))
            health_status["checks"]["database"] = {
                "status": "healthy",
                "message": "Database connection successful"
            }
            break
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
    
    # Response time check
    response_time = round((time.time() - start_time) * 1000, 2)
    health_status["checks"]["response_time"] = {
        "status": "healthy" if response_time < 1000 else "warning",
        "value": f"{response_time}ms"
    }
    
    return health_status


@app.get("/health/live")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes-style readiness probe with database check"""
    from app.core.database import get_db
    from sqlalchemy import text
    
    try:
        async for db in get_db():
            await db.execute(text("SELECT 1"))
            return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong"}


# Include API routers
app.include_router(
    projects.router,
    prefix=f"{settings.api_v1_str}/projects",
    tags=["projects"]
)

app.include_router(
    env_vars.router,
    prefix=f"{settings.api_v1_str}/env-vars",
    tags=["environment variables"]
)

app.include_router(
    exports.router,
    prefix=f"{settings.api_v1_str}/exports",
    tags=["exports"]
)

app.include_router(
    imports.router,
    prefix=f"{settings.api_v1_str}/imports",
    tags=["imports"]
)

app.include_router(
    variable_history.router,
    prefix=f"{settings.api_v1_str}/history",
    tags=["variable-history"]
)

app.include_router(
    search.router,
    prefix=f"{settings.api_v1_str}/search",
    tags=["search"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8088,
        reload=settings.debug,
        workers=None,  # Use None to disable multiprocessing
        loop="asyncio",
        log_level="info"
    ) 