import os

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from dotenv import load_dotenv
from jose import jwt
from jose import JWTError
from sqlalchemy import delete, select

from database import new_session
from models.auth import BlacklistedTokenOrm, RefreshTokenOrm
from repositories.user import UserRepository




load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', 30))




class AuthRepository:
    """Репозиторий для работы с аутентификацией."""
    
    @classmethod
    async def create_refresh_token(cls, user_id: int) -> str:
        """Создает новый refresh токен для пользователя."""
        async with new_session() as session:
            # Удаляем старые refresh токены пользователя
            delete_query = delete(RefreshTokenOrm).where(RefreshTokenOrm.user_id == user_id)
            await session.execute(delete_query)
            
            # Создаем новый токен
            refresh_token = jwt.encode(
                {"sub": str(user_id), "type": "refresh"}, 
                SECRET_KEY, 
                algorithm=ALGORITHM
            )
            expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            
            refresh_token_orm = RefreshTokenOrm(
                user_id=user_id,
                token=refresh_token,
                expires_at=expires_at
            )
            
            session.add(refresh_token_orm)
            await session.commit()
            
            return refresh_token
    
    
    @classmethod
    async def revoke_refresh_token(cls, user_id: int):
        """Отзывает refresh токен пользователя."""
        async with new_session() as session:
            query = delete(RefreshTokenOrm).where(RefreshTokenOrm.user_id == user_id)
            await session.execute(query)
            await session.commit()
    
    
    @classmethod
    async def get_user_by_refresh_token(cls, refresh_token: str):
        """Получает пользователя по refresh токену."""
        async with new_session() as session:
            query = select(RefreshTokenOrm).where(RefreshTokenOrm.token == refresh_token)
            result = await session.execute(query)
            refresh_token_orm = result.scalars().first()
            
            if not refresh_token_orm or refresh_token_orm.expires_at < datetime.now(timezone.utc):
                return None
            
            return await UserRepository.get_user_by_id(refresh_token_orm.user_id)
    
    
    @classmethod
    async def add_to_blacklist(cls, token: str):
        """Добавляет токен в черный список."""
        async with new_session() as session:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
                
            except JWTError:
                return

            # Проверяем, не добавлен ли уже токен
            query = select(BlacklistedTokenOrm).where(BlacklistedTokenOrm.token == token)
            result = await session.execute(query)
            if result.scalars().first():
                return

            blacklisted_token = BlacklistedTokenOrm(
                token=token,
                expires_at=expires_at,
                created_at=datetime.now(timezone.utc)
            )
            
            session.add(blacklisted_token)
            await session.commit()
    
    
    @classmethod
    async def is_token_blacklisted(cls, token: str) -> bool:
        """Проверяет, находится ли токен в черном списке."""
        async with new_session() as session:
            # Очищаем просроченные токены
            cleanup_query = delete(BlacklistedTokenOrm).where(
                BlacklistedTokenOrm.expires_at < datetime.now(timezone.utc)
            )
            await session.execute(cleanup_query)
            await session.commit()
            
            # Проверяем текущий токен
            query = select(BlacklistedTokenOrm).where(BlacklistedTokenOrm.token == token)
            result = await session.execute(query)
            return result.scalars().first() is not None