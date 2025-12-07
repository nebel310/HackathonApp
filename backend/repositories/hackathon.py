from datetime import datetime
from datetime import timezone
from typing import List, Optional, Tuple

from sqlalchemy import select, update, delete, func, or_
from sqlalchemy.orm import selectinload

from database import new_session
from models.hackathon import HackathonOrm, HackathonRegistrationOrm, HackathonSkillOrm
from models.team import TeamOrm
from schemas.hackathon import (
    HackathonCreate, 
    HackathonUpdate, 
    HackathonListFilters,
    HackathonSkillCreate
)




class HackathonRepository:
    """Репозиторий для работы с хакатонами."""
    
    @classmethod
    async def create_hackathon(cls, hackathon_data: HackathonCreate) -> HackathonOrm:
        """Создает новый хакатон."""
        async with new_session() as session:
            hackathon = HackathonOrm(**hackathon_data.model_dump())
            
            session.add(hackathon)
            await session.flush()
            await session.commit()
            await session.refresh(hackathon)
            
            return hackathon
    
    
    @classmethod
    async def get_hackathon_by_id(cls, hackathon_id: int) -> Optional[HackathonOrm]:
        """Получает хакатон по ID."""
        async with new_session() as session:
            query = select(HackathonOrm).where(HackathonOrm.id == hackathon_id)
            result = await session.execute(query)
            return result.scalars().first()
    
    
    @classmethod
    async def get_hackathon_with_details(cls, hackathon_id: int) -> Optional[Tuple[HackathonOrm, int, int]]:
        """Получает хакатон с количеством регистраций и команд."""
        async with new_session() as session:
            # Получаем хакатон
            hackathon_query = select(HackathonOrm).where(HackathonOrm.id == hackathon_id)
            hackathon_result = await session.execute(hackathon_query)
            hackathon = hackathon_result.scalars().first()
            
            if not hackathon:
                return None
            
            # Считаем регистрации
            registrations_query = select(func.count(HackathonRegistrationOrm.id)).where(
                HackathonRegistrationOrm.hackathon_id == hackathon_id
            )
            registrations_result = await session.execute(registrations_query)
            registration_count = registrations_result.scalar() or 0
            
            # Считаем команды
            teams_query = select(func.count(TeamOrm.id)).where(TeamOrm.hackathon_id == hackathon_id)
            teams_result = await session.execute(teams_query)
            team_count = teams_result.scalar() or 0
            
            return hackathon, registration_count, team_count
    
    
    @classmethod
    async def update_hackathon(
        cls, 
        hackathon_id: int, 
        update_data: HackathonUpdate
    ) -> Optional[HackathonOrm]:
        """Обновляет данные хакатона."""
        async with new_session() as session:
            # Проверяем существование хакатона
            query = select(HackathonOrm).where(HackathonOrm.id == hackathon_id)
            result = await session.execute(query)
            hackathon = result.scalars().first()
            
            if not hackathon:
                return None
            
            # Обновляем только переданные поля
            update_dict = update_data.model_dump(exclude_unset=True)
            if update_dict:
                stmt = (
                    update(HackathonOrm)
                    .where(HackathonOrm.id == hackathon_id)
                    .values(**update_dict, updated_at=datetime.now(timezone.utc))
                )
                await session.execute(stmt)
                await session.commit()
            
            # Возвращаем обновленный хакатон
            query = select(HackathonOrm).where(HackathonOrm.id == hackathon_id)
            result = await session.execute(query)
            return result.scalars().first()
    
    
    @classmethod
    async def delete_hackathon(cls, hackathon_id: int) -> bool:
        """Удаляет хакатон по ID."""
        async with new_session() as session:
            query = select(HackathonOrm).where(HackathonOrm.id == hackathon_id)
            result = await session.execute(query)
            hackathon = result.scalars().first()
            
            if not hackathon:
                return False
            
            await session.delete(hackathon)
            await session.commit()
            return True
    
    
    @classmethod
    async def get_hackathons(
        cls, 
        filters: HackathonListFilters,
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[HackathonOrm], int]:
        """Получает хакатоны с фильтрами и пагинацией."""
        async with new_session() as session:
            # Базовый запрос
            query = select(HackathonOrm)
            
            # Применяем фильтры
            if filters.status:
                query = query.where(HackathonOrm.status == filters.status)
            
            if filters.start_date_from:
                query = query.where(HackathonOrm.start_date >= filters.start_date_from)
            
            if filters.start_date_to:
                query = query.where(HackathonOrm.start_date <= filters.start_date_to)
            
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        HackathonOrm.name.ilike(search_term),
                        HackathonOrm.description.ilike(search_term)
                    )
                )
            
            # Считаем общее количество
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Применяем сортировку и пагинацию
            query = query.order_by(HackathonOrm.start_date.desc()).offset(skip).limit(limit)
            
            result = await session.execute(query)
            hackathons = list(result.scalars().all())
            
            return hackathons, total
    
    
    @classmethod
    async def register_for_hackathon(cls, hackathon_id: int, user_id: int) -> Optional[HackathonRegistrationOrm]:
        """Регистрирует пользователя на хакатон."""
        async with new_session() as session:
            # Проверяем существование хакатона
            hackathon_query = select(HackathonOrm).where(HackathonOrm.id == hackathon_id)
            hackathon_result = await session.execute(hackathon_query)
            hackathon = hackathon_result.scalars().first()
            
            if not hackathon:
                raise ValueError("Хакатон не найден")
            
            # Проверяем, что хакатон в статусе регистрации
            if hackathon.status != 'registration':
                raise ValueError("Регистрация на этот хакатон закрыта")
            
            # Проверяем, не зарегистрирован ли пользователь уже
            existing_reg_query = select(HackathonRegistrationOrm).where(
                HackathonRegistrationOrm.hackathon_id == hackathon_id,
                HackathonRegistrationOrm.user_id == user_id
            )
            existing_reg_result = await session.execute(existing_reg_query)
            existing_reg = existing_reg_result.scalars().first()
            
            if existing_reg:
                raise ValueError("Пользователь уже зарегистрирован на этот хакатон")
            
            # Создаем регистрацию
            registration = HackathonRegistrationOrm(
                hackathon_id=hackathon_id,
                user_id=user_id,
                registration_date=datetime.now(timezone.utc)
            )
            
            session.add(registration)
            await session.flush()
            await session.commit()
            await session.refresh(registration)
            
            return registration
    
    
    @classmethod
    async def unregister_from_hackathon(cls, hackathon_id: int, user_id: int) -> bool:
        """Отменяет регистрацию пользователя на хакатон."""
        async with new_session() as session:
            query = select(HackathonRegistrationOrm).where(
                HackathonRegistrationOrm.hackathon_id == hackathon_id,
                HackathonRegistrationOrm.user_id == user_id
            )
            result = await session.execute(query)
            registration = result.scalars().first()
            
            if not registration:
                return False
            
            await session.delete(registration)
            await session.commit()
            return True
    
    
    @classmethod
    async def get_hackathon_registrations(
        cls, 
        hackathon_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[HackathonRegistrationOrm], int]:
        """Получает регистрации на хакатон с пагинацией."""
        async with new_session() as session:
            # Запрос регистраций
            query = (
                select(HackathonRegistrationOrm)
                .where(HackathonRegistrationOrm.hackathon_id == hackathon_id)
                .order_by(HackathonRegistrationOrm.registration_date.desc())
            )
            
            # Считаем общее количество
            count_query = select(func.count()).where(
                HackathonRegistrationOrm.hackathon_id == hackathon_id
            )
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Применяем пагинацию
            query = query.offset(skip).limit(limit)
            
            result = await session.execute(query)
            registrations = list(result.scalars().all())
            
            return registrations, total
    
    
    @classmethod
    async def get_user_hackathon_registrations(cls, user_id: int) -> List[HackathonRegistrationOrm]:
        """Получает регистрации пользователя на хакатоны."""
        async with new_session() as session:
            query = (
                select(HackathonRegistrationOrm)
                .where(HackathonRegistrationOrm.user_id == user_id)
                .order_by(HackathonRegistrationOrm.registration_date.desc())
            )
            result = await session.execute(query)
            return list(result.scalars().all())
    
    
    @classmethod
    async def add_hackathon_skill(
        cls, 
        hackathon_id: int, 
        skill_data: HackathonSkillCreate
    ) -> Optional[HackathonSkillOrm]:
        """Добавляет навык хакатону."""
        async with new_session() as session:
            # Проверяем существование хакатона
            hackathon = await cls.get_hackathon_by_id(hackathon_id)
            if not hackathon:
                return None
            
            # Проверяем, не существует ли уже такой навык у хакатона
            query = select(HackathonSkillOrm).where(
                HackathonSkillOrm.hackathon_id == hackathon_id,
                HackathonSkillOrm.skill_name == skill_data.skill_name
            )
            result = await session.execute(query)
            existing_skill = result.scalars().first()
            
            if existing_skill:
                raise ValueError("У хакатона уже есть такой навык")
            
            skill = HackathonSkillOrm(
                hackathon_id=hackathon_id,
                skill_name=skill_data.skill_name,
                priority=skill_data.priority
            )
            
            session.add(skill)
            await session.commit()
            await session.refresh(skill)
            return skill
    
    
    @classmethod
    async def remove_hackathon_skill(cls, hackathon_id: int, skill_id: int) -> bool:
        """Удаляет навык хакатона."""
        async with new_session() as session:
            query = select(HackathonSkillOrm).where(
                HackathonSkillOrm.id == skill_id,
                HackathonSkillOrm.hackathon_id == hackathon_id
            )
            result = await session.execute(query)
            skill = result.scalars().first()
            
            if not skill:
                return False
            
            await session.delete(skill)
            await session.commit()
            return True
    
    
    @classmethod
    async def get_hackathon_skills(cls, hackathon_id: int) -> List[HackathonSkillOrm]:
        """Получает все навыки хакатона."""
        async with new_session() as session:
            query = (
                select(HackathonSkillOrm)
                .where(HackathonSkillOrm.hackathon_id == hackathon_id)
                .order_by(HackathonSkillOrm.priority, HackathonSkillOrm.created_at)
            )
            result = await session.execute(query)
            return list(result.scalars().all())