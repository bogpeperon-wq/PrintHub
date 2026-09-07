"""
User Service - manages user profiles and preferences.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.models.base import User


class UserService:
    """Service for managing user profiles."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> User:
        """Get existing user or create new one."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                display_name=display_name or username,
            )
            self.session.add(user)
            await self.session.flush()
        
        return user
    
    async def update_user_address(
        self,
        telegram_id: int,
        building: Optional[str] = None,
        entrance: Optional[str] = None,
        room: Optional[str] = None,
    ) -> User:
        """Update user delivery address."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one()
        
        if building is not None:
            user.building = building
        if entrance is not None:
            user.entrance = entrance
        if room is not None:
            user.room = room
        
        await self.session.flush()
        return user
    
    async def set_free_user(self, telegram_id: int, is_free: bool = True) -> User:
        """Set user as free (no payment required)."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one()
        user.is_free_user = is_free
        await self.session.flush()
        return user
    
    async def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def needs_address(self, telegram_id: int) -> bool:
        """Check if user needs to provide address."""
        user = await self.get_user(telegram_id)
        if not user:
            return True
        return not (user.building and user.entrance and user.room)
