from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import List, Optional

from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload

from database import new_session
from models.user import UserOrm, UserSkillOrm, UserRole
from schemas.user import UserCreate, UserUpdate, UserSkillCreate




class UserRepository:
    """Репозиторий для работы с пользователями."""
    
    @classmethod
    async def get_user_by_telegram_username(cls, telegram_username: str) -> Optional[UserOrm]:
        """Получает пользователя по Telegram username."""
        async with new_session() as session:
            query = (
                select(UserOrm)
                .where(UserOrm.telegram_username == telegram_username)
                .options(selectinload(UserOrm.skills))
            )
            result = await session.execute(query)
            return result.scalars().first()
    
    
    @classmethod
    async def get_user_by_id(cls, user_id: int) -> Optional[UserOrm]:
        """Получает пользователя по ID."""
        async with new_session() as session:
            query = (
                select(UserOrm)
                .where(UserOrm.id == user_id)
                .options(selectinload(UserOrm.skills))
            )
            result = await session.execute(query)
            return result.scalars().first()
    
    
    @classmethod
    async def create_user(cls, user_data: UserCreate) -> UserOrm:
        """Создает нового пользователя."""
        async with new_session() as session:
            # Проверяем, существует ли пользователь
            existing_user = await cls.get_user_by_telegram_username(user_data.telegram_username)
            if existing_user:
                raise ValueError("Пользователь с таким Telegram username уже существует")
            
            user = UserOrm(
                telegram_username=user_data.telegram_username,
                role=UserRole.USER
            )
            
            session.add(user)
            await session.flush()
            await session.commit()
            
            # Возвращаем пользователя с навыками
            query = (
                select(UserOrm)
                .where(UserOrm.id == user.id)
                .options(selectinload(UserOrm.skills))
            )
            result = await session.execute(query)
            return result.scalars().first()
    
    
    @classmethod
    async def update_user(cls, user_id: int, update_data: UserUpdate) -> Optional[UserOrm]:
        """Обновляет данные пользователя."""
        async with new_session() as session:
            # Получаем пользователя
            query = select(UserOrm).where(UserOrm.id == user_id)
            result = await session.execute(query)
            user = result.scalars().first()
            
            if not user:
                return None
            
            # Обновляем только переданные поля
            update_dict = update_data.model_dump(exclude_unset=True)
            if update_dict:
                # Конвертируем contacts в строку JSON если это dict
                if 'contacts' in update_dict and isinstance(update_dict['contacts'], dict):
                    import json
                    update_dict['contacts'] = json.dumps(update_dict['contacts'])
                
                stmt = (
                    update(UserOrm)
                    .where(UserOrm.id == user_id)
                    .values(**update_dict, updated_at=datetime.now(timezone.utc))
                )
                await session.execute(stmt)
                await session.commit()
            
            # Возвращаем обновленного пользователя
            query = (
                select(UserOrm)
                .where(UserOrm.id == user_id)
                .options(selectinload(UserOrm.skills))
            )
            result = await session.execute(query)
            return result.scalars().first()
    
    
    @classmethod
    async def delete_user(cls, user_id: int) -> bool:
        """Удаляет пользователя по ID."""
        async with new_session() as session:
            query = select(UserOrm).where(UserOrm.id == user_id)
            result = await session.execute(query)
            user = result.scalars().first()
            
            if not user:
                return False
            
            await session.delete(user)
            await session.commit()
            return True
    
    
    @classmethod
    async def get_all_users(
        cls, 
        skip: int = 0, 
        limit: int = 100,
        role: Optional[str] = None
    ) -> List[UserOrm]:
        """Получает всех пользователей с пагинацией."""
        async with new_session() as session:
            query = select(UserOrm).options(selectinload(UserOrm.skills))
            
            if role:
                query = query.where(UserOrm.role == role)
            
            query = query.offset(skip).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())
    
    
    @classmethod
    async def update_user_role(cls, user_id: int, new_role: UserRole) -> Optional[UserOrm]:
        """Обновляет роль пользователя."""
        async with new_session() as session:
            # Проверяем существование пользователя
            query = select(UserOrm).where(UserOrm.id == user_id)
            result = await session.execute(query)
            user = result.scalars().first()
            
            if not user:
                return None
            
            # Обновляем роль
            stmt = (
                update(UserOrm)
                .where(UserOrm.id == user_id)
                .values(role=new_role, updated_at=datetime.now(timezone.utc))
            )
            await session.execute(stmt)
            await session.commit()
            
            # Возвращаем обновленного пользователя
            query = (
                select(UserOrm)
                .where(UserOrm.id == user_id)
                .options(selectinload(UserOrm.skills))
            )
            result = await session.execute(query)
            return result.scalars().first()
    
    
    @classmethod
    async def add_user_skill(cls, user_id: int, skill_data: UserSkillCreate) -> Optional[UserSkillOrm]:
        """Добавляет навык пользователю."""
        async with new_session() as session:
            # Проверяем существование пользователя
            user = await cls.get_user_by_id(user_id)
            if not user:
                return None
            
            # Проверяем, не существует ли уже такой навык у пользователя
            query = (
                select(UserSkillOrm)
                .where(
                    UserSkillOrm.user_id == user_id,
                    UserSkillOrm.skill_name == skill_data.skill_name
                )
            )
            result = await session.execute(query)
            existing_skill = result.scalars().first()
            
            if existing_skill:
                raise ValueError("У пользователя уже есть такой навык")
            
            skill = UserSkillOrm(
                user_id=user_id,
                skill_name=skill_data.skill_name
            )
            
            session.add(skill)
            await session.commit()
            await session.refresh(skill)
            return skill
    
    
    @classmethod
    async def remove_user_skill(cls, user_id: int, skill_id: int) -> bool:
        """Удаляет навык пользователя."""
        async with new_session() as session:
            query = (
                select(UserSkillOrm)
                .where(
                    UserSkillOrm.id == skill_id,
                    UserSkillOrm.user_id == user_id
                )
            )
            result = await session.execute(query)
            skill = result.scalars().first()
            
            if not skill:
                return False
            
            await session.delete(skill)
            await session.commit()
            return True
    
    
    @classmethod
    async def get_user_skills(cls, user_id: int) -> List[UserSkillOrm]:
        """Получает все навыки пользователя."""
        async with new_session() as session:
            query = (
                select(UserSkillOrm)
                .where(UserSkillOrm.user_id == user_id)
                .order_by(UserSkillOrm.created_at)
            )
            result = await session.execute(query)
            return list(result.scalars().all())