"""
Multi-Tenant AI Agent Platform - Main Application Entry Point.

FastAPI application with database lifecycle management.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    print(f"🚀 Starting {settings.PROJECT_NAME}...")
    print(f"📍 Environment: {settings.APP_ENV}")
    
    try:
        await init_db()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("⚠️  Make sure DATABASE_URL is set correctly in .env")
        # Don't raise - allow app to start for debugging
    
    yield
    
    # Shutdown
    await close_db()
    print(f"👋 {settings.PROJECT_NAME} stopped")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-Tenant AI Agent Platform for Revenue Operations",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "version": "0.1.0"
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs": "/docs",
        "health": "/health"
    }


# Import and include routers
from app.api.v1.tenants import router as tenants_router
from app.api.v1.users import router as users_router
from app.api.v1.invitations import router as invitations_router
from app.api.v1.agents import router as agents_router

app.include_router(tenants_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(invitations_router, prefix=settings.API_V1_PREFIX)
app.include_router(agents_router, prefix=settings.API_V1_PREFIX)
