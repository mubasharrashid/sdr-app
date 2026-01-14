"""
Database Session Management.

Provides async database sessions for FastAPI dependency injection.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator

from app.core.config import settings


# Create async engine
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.APP_DEBUG,  # Log SQL in debug mode
    poolclass=NullPool,  # Recommended for serverless/Supabase
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database connection (for startup)."""
    async with engine.begin() as conn:
        # Test connection
        await conn.execute("SELECT 1")
    print("✅ Database connection established")


async def close_db() -> None:
    """Close database connections (for shutdown)."""
    await engine.dispose()
    print("🔌 Database connections closed")
