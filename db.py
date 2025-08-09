from typing import List
from typing import Optional

from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class DbBase(AsyncAttrs, DeclarativeBase):
    pass


class User(DbBase):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(primary_key=True)
    is_irl: Mapped[bool] = mapped_column(default=True)


engine = create_async_engine("sqlite+aiosqlite:///database.db")
async_session = async_sessionmaker(engine, expire_on_commit=False)


class DatabaseManager:
    @staticmethod
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(DbBase.metadata.create_all)

    @staticmethod
    async def get_session() -> async_sessionmaker[AsyncSession]:
        return async_session


class UserRepository:
    @staticmethod
    async def create_user(user_id: int, is_irl: Optional[bool] = None) -> User:
        async with async_session() as session:
            user = User(user_id=user_id, is_irl=is_irl)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    @staticmethod
    async def get_user_by_id(user_id: int) -> Optional[User]:
        async with async_session() as session:
            stmt = select(User).where(User.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def update_user_settings(current_user_id: int, **kwargs) -> bool:
        async with async_session() as session:
            stmt = update(User).where(User.user_id == current_user_id).values(**kwargs)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    @staticmethod
    async def delete_user(user_id: int) -> bool:
        async with async_session() as session:
            stmt = delete(User).where(User.user_id == user_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    @staticmethod
    async def get_all_users() -> List[User]:
        async with async_session() as session:
            stmt = select(User)
            return list((await session.execute(stmt)).scalars().all())
