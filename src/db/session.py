"""Database session management."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import sessionmaker

from src.domain.models.base import Base


class Database:
    """Database connection and session manager."""
    
    def __init__(self, database_url: str, pool_size: int = 10, max_overflow: int = 20):
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=False,
            future=True,
        )
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    
    async def create_tables(self) -> None:
        """Create all tables in the database."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self) -> None:
        """Drop all tables in the database."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session for dependency injection."""
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def get_session_no_commit(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session without automatic commit (for manual transaction control)."""
        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close database connections."""
        await self.engine.dispose()


# Global database instance
db: Database | None = None


def get_database() -> Database:
    """Get global database instance."""
    global db
    if db is None:
        raise RuntimeError("Database not initialized. Call init_database first.")
    return db


def init_database(database_url: str, pool_size: int = 10, max_overflow: int = 20) -> Database:
    """Initialize global database instance."""
    global db
    db = Database(database_url, pool_size, max_overflow)
    return db
