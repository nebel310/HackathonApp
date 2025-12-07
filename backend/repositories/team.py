from datetime import datetime
from datetime import timezone
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import select, update, delete, func, or_
from sqlalchemy.orm import selectinload

from database import new_session
from models.team import TeamOrm, TeamMemberOrm, TeamInvitationOrm, TeamMemberRole, InvitationStatus
from models.hackathon import HackathonOrm, HackathonRegistrationOrm
from models.user import UserOrm, UserSkillOrm
from schemas.team import TeamCreate, TeamUpdate, TeamInvitationCreate, TeamInvitationUpdate, UserSearchFilters




class TeamRepository:
    """Репозиторий для работы с командами."""
    
    @classmethod
    async def create_team(cls, team_data: TeamCreate, captain_id: int) -> Optional[TeamOrm]:
        """Создает новую команду."""
        async with new_session() as session:
            # Проверяем существование хакатона
            hackathon_query = select(HackathonOrm).where(HackathonOrm.id == team_data.hackathon_id)
            hackathon_result = await session.execute(hackathon_query)
            hackathon = hackathon_result.scalars().first()
            
            if not hackathon:
                raise ValueError("Хакатон не найден")
            
            # Проверяем, что хакатон в статусе регистрации
            if hackathon.status != 'registration':
                raise ValueError("Нельзя создать команду для хакатона не в статусе регистрации")
            
            # Проверяем, что капитан зарегистрирован на хакатон
            registration_query = select(HackathonRegistrationOrm).where(
                HackathonRegistrationOrm.hackathon_id == team_data.hackathon_id,
                HackathonRegistrationOrm.user_id == captain_id
            )
            registration_result = await session.execute(registration_query)
            registration = registration_result.scalars().first()
            
            if not registration:
                raise ValueError("Вы не зарегистрированы на этот хакатон")
            
            # Проверяем уникальность названия команды в рамках хакатона
            team_name_query = select(TeamOrm).where(
                TeamOrm.hackathon_id == team_data.hackathon_id,
                TeamOrm.name == team_data.name
            )
            team_name_result = await session.execute(team_name_query)
            existing_team = team_name_result.scalars().first()
            
            if existing_team:
                raise ValueError("Команда с таким названием уже существует в этом хакатоне")
            
            # Создаем команду
            team = TeamOrm(
                name=team_data.name,
                description=team_data.description,
                hackathon_id=team_data.hackathon_id,
                captain_id=captain_id
            )
            
            session.add(team)
            await session.flush()
            
            # Добавляем капитана в участники команды
            team_member = TeamMemberOrm(
                team_id=team.id,
                user_id=captain_id,
                role=TeamMemberRole.CAPTAIN,
                joined_at=datetime.now(timezone.utc)
            )
            
            session.add(team_member)
            
            # Обновляем регистрацию пользователя, указывая команду
            registration_update = (
                update(HackathonRegistrationOrm)
                .where(
                    HackathonRegistrationOrm.hackathon_id == team_data.hackathon_id,
                    HackathonRegistrationOrm.user_id == captain_id
                )
                .values(team_id=team.id)
            )
            await session.execute(registration_update)
            
            await session.commit()
            await session.refresh(team)
            
            return team
    
    
    @classmethod
    async def get_team_by_id(cls, team_id: int) -> Optional[TeamOrm]:
        """Получает команду по ID."""
        async with new_session() as session:
            query = select(TeamOrm).where(TeamOrm.id == team_id)
            result = await session.execute(query)
            return result.scalars().first()
    
    
    @classmethod
    async def get_team_with_details(cls, team_id: int) -> Optional[Dict[str, Any]]:
        """Получает команду с детальной информацией."""
        async with new_session() as session:
            # Получаем команду
            team_query = select(TeamOrm).where(TeamOrm.id == team_id)
            team_result = await session.execute(team_query)
            team = team_result.scalars().first()
            
            if not team:
                return None
            
            # Получаем участников команды с информацией о пользователях
            members_query = (
                select(TeamMemberOrm, UserOrm)
                .join(UserOrm, TeamMemberOrm.user_id == UserOrm.id)
                .where(TeamMemberOrm.team_id == team_id)
                .order_by(TeamMemberOrm.joined_at)
            )
            members_result = await session.execute(members_query)
            members_data = members_result.all()
            
            # Формируем информацию об участниках
            members = []
            for team_member, user in members_data:
                members.append({
                    'id': team_member.id,
                    'user_id': user.id,
                    'role': team_member.role,
                    'joined_at': team_member.joined_at,
                    'user_telegram_username': user.telegram_username,
                    'user_full_name': user.full_name,
                    'user_position': user.position
                })
            
            # Получаем информацию о капитане
            captain_query = select(UserOrm).where(UserOrm.id == team.captain_id)
            captain_result = await session.execute(captain_query)
            captain = captain_result.scalars().first()
            
            return {
                'id': team.id,
                'name': team.name,
                'description': team.description,
                'hackathon_id': team.hackathon_id,
                'captain_id': team.captain_id,
                'created_at': team.created_at,
                'updated_at': team.updated_at,
                'captain_telegram_username': captain.telegram_username if captain else None,
                'members': members
            }
    
    
    @classmethod
    async def update_team(cls, team_id: int, update_data: TeamUpdate, user_id: int) -> Optional[TeamOrm]:
        """Обновляет данные команды."""
        async with new_session() as session:
            # Проверяем, что пользователь - капитан команды
            team_query = select(TeamOrm).where(TeamOrm.id == team_id)
            team_result = await session.execute(team_query)
            team = team_result.scalars().first()
            
            if not team:
                return None
            
            if team.captain_id != user_id:
                raise ValueError("Только капитан может редактировать команду")
            
            # Обновляем только переданные поля
            update_dict = update_data.model_dump(exclude_unset=True)
            if update_dict:
                stmt = (
                    update(TeamOrm)
                    .where(TeamOrm.id == team_id)
                    .values(**update_dict, updated_at=datetime.now(timezone.utc))
                )
                await session.execute(stmt)
                await session.commit()
            
            # Возвращаем обновленную команду
            query = select(TeamOrm).where(TeamOrm.id == team_id)
            result = await session.execute(query)
            return result.scalars().first()
    
    
    @classmethod
    async def delete_team(cls, team_id: int, user_id: int) -> bool:
        """Удаляет команду."""
        async with new_session() as session:
            # Проверяем, что пользователь - капитан команды
            team_query = select(TeamOrm).where(TeamOrm.id == team_id)
            team_result = await session.execute(team_query)
            team = team_result.scalars().first()
            
            if not team:
                return False
            
            if team.captain_id != user_id:
                raise ValueError("Только капитан может удалить команду")
            
            # Удаляем команду
            await session.delete(team)
            await session.commit()
            return True
    
    
    @classmethod
    async def get_hackathon_teams(
        cls, 
        hackathon_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Получает команды хакатона с пагинацией."""
        async with new_session() as session:
            # Базовый запрос команд
            teams_query = (
                select(TeamOrm)
                .where(TeamOrm.hackathon_id == hackathon_id)
                .order_by(TeamOrm.created_at.desc())
            )
            
            # Считаем общее количество
            count_query = select(func.count()).where(TeamOrm.hackathon_id == hackathon_id)
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Применяем пагинацию
            teams_query = teams_query.offset(skip).limit(limit)
            teams_result = await session.execute(teams_query)
            teams = list(teams_result.scalars().all())
            
            # Получаем детальную информацию о каждой команде
            teams_with_details = []
            for team in teams:
                team_details = await cls.get_team_with_details(team.id)
                if team_details:
                    teams_with_details.append(team_details)
            
            return teams_with_details, total
    
    
    @classmethod
    async def add_team_member(cls, team_id: int, user_id: int, role: TeamMemberRole = TeamMemberRole.MEMBER) -> Optional[TeamMemberOrm]:
        """Добавляет участника в команду."""
        async with new_session() as session:
            # Проверяем существование команды
            team = await cls.get_team_by_id(team_id)
            if not team:
                raise ValueError("Команда не найдена")
            
            # Проверяем, что пользователь зарегистрирован на хакатон
            registration_query = select(HackathonRegistrationOrm).where(
                HackathonRegistrationOrm.hackathon_id == team.hackathon_id,
                HackathonRegistrationOrm.user_id == user_id
            )
            registration_result = await session.execute(registration_query)
            registration = registration_result.scalars().first()
            
            if not registration:
                raise ValueError("Пользователь не зарегистрирован на этот хакатон")
            
            # Проверяем, не состоит ли пользователь уже в команде
            existing_member_query = select(TeamMemberOrm).where(
                TeamMemberOrm.team_id == team_id,
                TeamMemberOrm.user_id == user_id
            )
            existing_member_result = await session.execute(existing_member_query)
            existing_member = existing_member_result.scalars().first()
            
            if existing_member:
                raise ValueError("Пользователь уже состоит в команде")
            
            # Проверяем максимальный размер команды
            members_count_query = select(func.count(TeamMemberOrm.id)).where(TeamMemberOrm.team_id == team_id)
            members_count_result = await session.execute(members_count_query)
            members_count = members_count_result.scalar() or 0
            
            if members_count >= team.max_team_size:
                raise ValueError(f"Команда уже достигла максимального размера ({team.max_team_size} человек)")
            
            # Добавляем участника
            team_member = TeamMemberOrm(
                team_id=team_id,
                user_id=user_id,
                role=role,
                joined_at=datetime.now(timezone.utc)
            )
            
            session.add(team_member)
            
            # Обновляем регистрацию пользователя, указывая команду
            registration_update = (
                update(HackathonRegistrationOrm)
                .where(
                    HackathonRegistrationOrm.hackathon_id == team.hackathon_id,
                    HackathonRegistrationOrm.user_id == user_id
                )
                .values(team_id=team_id)
            )
            await session.execute(registration_update)
            
            await session.commit()
            await session.refresh(team_member)
            
            return team_member
    
    
    @classmethod
    async def remove_team_member(cls, team_id: int, member_user_id: int, remover_user_id: int) -> bool:
        """Удаляет участника из команды."""
        async with new_session() as session:
            # Проверяем существование команды
            team = await cls.get_team_by_id(team_id)
            if not team:
                raise ValueError("Команда не найдена")
            
            # Проверяем права: либо пользователь удаляет себя, либо капитан удаляет участника
            if member_user_id != remover_user_id and team.captain_id != remover_user_id:
                raise ValueError("Недостаточно прав для удаления участника")
            
            # Не даем капитану удалить себя (нужно передать капитана)
            if member_user_id == team.captain_id:
                raise ValueError("Капитан не может удалить себя из команды")
            
            # Находим участника
            member_query = select(TeamMemberOrm).where(
                TeamMemberOrm.team_id == team_id,
                TeamMemberOrm.user_id == member_user_id
            )
            member_result = await session.execute(member_query)
            member = member_result.scalars().first()
            
            if not member:
                return False
            
            # Удаляем участника
            await session.delete(member)
            
            # Обновляем регистрацию пользователя, убирая команду
            registration_update = (
                update(HackathonRegistrationOrm)
                .where(
                    HackathonRegistrationOrm.hackathon_id == team.hackathon_id,
                    HackathonRegistrationOrm.user_id == member_user_id
                )
                .values(team_id=None)
            )
            await session.execute(registration_update)
            
            await session.commit()
            return True
    
    
    @classmethod
    async def create_invitation(
        cls, 
        invitation_data: TeamInvitationCreate, 
        inviter_id: int
    ) -> Optional[TeamInvitationOrm]:
        """Создает приглашение в команду."""
        async with new_session() as session:
            # Проверяем существование команды
            team = await cls.get_team_by_id(invitation_data.team_id)
            if not team:
                raise ValueError("Команда не найдена")
            
            # Проверяем, что приглашающий - капитан команды
            if team.captain_id != inviter_id:
                raise ValueError("Только капитан может приглашать в команду")
            
            # Проверяем, что приглашаемый не приглашает сам себя
            if inviter_id == invitation_data.invitee_id:
                raise ValueError("Нельзя пригласить самого себя")
            
            # Проверяем, что приглашаемый зарегистрирован на хакатон
            registration_query = select(HackathonRegistrationOrm).where(
                HackathonRegistrationOrm.hackathon_id == team.hackathon_id,
                HackathonRegistrationOrm.user_id == invitation_data.invitee_id
            )
            registration_result = await session.execute(registration_query)
            registration = registration_result.scalars().first()
            
            if not registration:
                raise ValueError("Пользователь не зарегистрирован на этот хакатон")
            
            # Проверяем, не состоит ли приглашаемый уже в команде
            existing_member_query = select(TeamMemberOrm).where(
                TeamMemberOrm.team_id == invitation_data.team_id,
                TeamMemberOrm.user_id == invitation_data.invitee_id
            )
            existing_member_result = await session.execute(existing_member_query)
            existing_member = existing_member_result.scalars().first()
            
            if existing_member:
                raise ValueError("Пользователь уже состоит в команде")
            
            # Проверяем, нет ли уже активного приглашения
            existing_invitation_query = select(TeamInvitationOrm).where(
                TeamInvitationOrm.team_id == invitation_data.team_id,
                TeamInvitationOrm.invitee_id == invitation_data.invitee_id,
                TeamInvitationOrm.status == InvitationStatus.PENDING
            )
            existing_invitation_result = await session.execute(existing_invitation_query)
            existing_invitation = existing_invitation_result.scalars().first()
            
            if existing_invitation:
                raise ValueError("Пользователю уже отправлено приглашение")
            
            # Создаем приглашение
            invitation = TeamInvitationOrm(
                team_id=invitation_data.team_id,
                inviter_id=inviter_id,
                invitee_id=invitation_data.invitee_id,
                message=invitation_data.message
            )
            
            session.add(invitation)
            await session.commit()
            await session.refresh(invitation)
            
            return invitation
    
    
    @classmethod
    async def update_invitation_status(
        cls, 
        invitation_id: int, 
        update_data: TeamInvitationUpdate, 
        user_id: int
    ) -> Optional[TeamInvitationOrm]:
        """Обновляет статус приглашения."""
        async with new_session() as session:
            # Получаем приглашение
            invitation_query = select(TeamInvitationOrm).where(TeamInvitationOrm.id == invitation_id)
            invitation_result = await session.execute(invitation_query)
            invitation = invitation_result.scalars().first()
            
            if not invitation:
                return None
            
            # Проверяем, что пользователь - получатель приглашения
            if invitation.invitee_id != user_id:
                raise ValueError("Только получатель может отвечать на приглашение")
            
            # Проверяем, что приглашение еще в статусе ожидания
            if invitation.status != InvitationStatus.PENDING:
                raise ValueError("Приглашение уже было обработано")
            
            # Обновляем статус
            invitation.status = update_data.status
            invitation.updated_at = datetime.now(timezone.utc)
            
            # Если приглашение принято, добавляем пользователя в команду
            if update_data.status == InvitationStatus.ACCEPTED:
                try:
                    await cls.add_team_member(invitation.team_id, user_id)
                except ValueError as e:
                    # Если не удалось добавить в команду, отменяем принятие приглашения
                    invitation.status = InvitationStatus.PENDING
                    await session.commit()
                    raise ValueError(f"Не удалось принять приглашение: {str(e)}")
            
            await session.commit()
            await session.refresh(invitation)
            
            return invitation
    
    
    @classmethod
    async def get_user_invitations(
        cls, 
        user_id: int,
        status: Optional[InvitationStatus] = None
    ) -> List[TeamInvitationOrm]:
        """Получает приглашения пользователя."""
        async with new_session() as session:
            query = select(TeamInvitationOrm).where(TeamInvitationOrm.invitee_id == user_id)
            
            if status:
                query = query.where(TeamInvitationOrm.status == status)
            
            query = query.order_by(TeamInvitationOrm.created_at.desc())
            result = await session.execute(query)
            return list(result.scalars().all())
    
    
    @classmethod
    async def get_team_invitations(cls, team_id: int) -> List[TeamInvitationOrm]:
        """Получает приглашения команды."""
        async with new_session() as session:
            query = (
                select(TeamInvitationOrm)
                .where(TeamInvitationOrm.team_id == team_id)
                .order_by(TeamInvitationOrm.created_at.desc())
            )
            result = await session.execute(query)
            return list(result.scalars().all())
    
    
    @classmethod
    async def search_users(
        cls, 
        filters: UserSearchFilters,
        hackathon_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Ищет пользователей по фильтрам."""
        async with new_session() as session:
            # Базовый запрос пользователей
            query = (
                select(UserOrm)
                .distinct()
            )
            
            # Фильтр по хакатону: только зарегистрированные пользователи
            if hackathon_id:
                subquery = (
                    select(HackathonRegistrationOrm.user_id)
                    .where(HackathonRegistrationOrm.hackathon_id == hackathon_id)
                    .subquery()
                )
                query = query.join(subquery, UserOrm.id == subquery.c.user_id)
            
            # Фильтр по навыкам
            if filters.skills and len(filters.skills) > 0:
                skills_subquery = (
                    select(UserSkillOrm.user_id)
                    .where(UserSkillOrm.skill_name.in_(filters.skills))
                    .group_by(UserSkillOrm.user_id)
                    .having(func.count(UserSkillOrm.id) >= len(filters.skills))
                    .subquery()
                )
                query = query.join(skills_subquery, UserOrm.id == skills_subquery.c.user_id)
            
            # Фильтр по текстовому поиску
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        UserOrm.telegram_username.ilike(search_term),
                        UserOrm.full_name.ilike(search_term),
                        UserOrm.position.ilike(search_term),
                        UserOrm.about.ilike(search_term)
                    )
                )
            
            # Фильтр по позиции
            if filters.position:
                position_term = f"%{filters.position}%"
                query = query.where(UserOrm.position.ilike(position_term))
            
            # Считаем общее количество
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Применяем сортировку и пагинацию
            query = query.order_by(UserOrm.created_at.desc()).offset(skip).limit(limit)
            
            result = await session.execute(query)
            users = list(result.scalars().all())
            
            # Форматируем результат
            users_data = []
            for user in users:
                # Получаем навыки пользователя
                skills_query = (
                    select(UserSkillOrm.skill_name)
                    .where(UserSkillOrm.user_id == user.id)
                    .order_by(UserSkillOrm.created_at)
                )
                skills_result = await session.execute(skills_query)
                skills = [skill[0] for skill in skills_result.all()]
                
                # Парсим контакты из JSON строки
                contacts = None
                if user.contacts:
                    import json
                    try:
                        contacts = json.loads(user.contacts)
                    except (json.JSONDecodeError, TypeError):
                        contacts = None
                
                users_data.append({
                    'id': user.id,
                    'telegram_username': user.telegram_username,
                    'full_name': user.full_name,
                    'position': user.position,
                    'about': user.about,
                    'contacts': contacts,
                    'skills': skills,
                    'created_at': user.created_at
                })
            
            return users_data, total