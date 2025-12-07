from typing import List, Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status

from repositories.team import TeamRepository
from schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamInvitationCreate,
    TeamInvitationResponse,
    TeamInvitationUpdate,
    UserSearchFilters,
    PaginatedUsersResponse,
    PaginatedTeamsResponse
)
from schemas.user import ErrorResponse, ValidationErrorResponse
from utils.security import get_current_user, get_current_admin_user




router = APIRouter(
    prefix="/teams",
    tags=['Команды']
)




@router.post(
    "",
    response_model=TeamResponse,
    status_code=201,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Ошибка создания команды"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        500: {"model": ErrorResponse}
    }
)
async def create_team(
    team_data: TeamCreate,
    current_user = Depends(get_current_user)
):
    """
    Создание новой команды.
    
    Создатель становится капитаном команды.
    Пользователь должен быть зарегистрирован на указанный хакатон.
    """
    try:
        team = await TeamRepository.create_team(team_data, current_user.id)
        team_details = await TeamRepository.get_team_with_details(team.id)
        return TeamResponse.model_validate(team_details)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Команда не найдена"},
        500: {"model": ErrorResponse}
    }
)
async def get_team(team_id: int):
    """
    Получение информации о команде.
    
    Доступно всем пользователям.
    """
    team_details = await TeamRepository.get_team_with_details(team_id)
    
    if not team_details:
        raise HTTPException(status_code=404, detail="Команда не найдена")
    
    return TeamResponse.model_validate(team_details)




@router.patch(
    "/{team_id}",
    response_model=TeamResponse,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Ошибка обновления"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        403: {"model": ErrorResponse, "description": "Недостаточно прав"},
        404: {"model": ErrorResponse, "description": "Команда не найдена"},
        500: {"model": ErrorResponse}
    }
)
async def update_team(
    team_id: int,
    update_data: TeamUpdate,
    current_user = Depends(get_current_user)
):
    """
    Обновление информации о команде.
    
    Доступно только капитану команды.
    Поддерживает частичное обновление (PATCH).
    """
    try:
        updated_team = await TeamRepository.update_team(team_id, update_data, current_user.id)
        
        if not updated_team:
            raise HTTPException(status_code=404, detail="Команда не найдена")
        
        team_details = await TeamRepository.get_team_with_details(team_id)
        return TeamResponse.model_validate(team_details)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




@router.delete(
    "/{team_id}",
    response_model=dict,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Ошибка удаления"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        403: {"model": ErrorResponse, "description": "Недостаточно прав"},
        404: {"model": ErrorResponse, "description": "Команда не найдена"},
        500: {"model": ErrorResponse}
    }
)
async def delete_team(
    team_id: int,
    current_user = Depends(get_current_user)
):
    """
    Удаление команды.
    
    Доступно только капитану команды.
    """
    try:
        deleted = await TeamRepository.delete_team(team_id, current_user.id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Команда не найдена")
        
        return {"success": True, "message": "Команда удалена"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




@router.get(
    "/hackathon/{hackathon_id}",
    response_model=PaginatedTeamsResponse,
    responses={
        500: {"model": ErrorResponse}
    }
)
async def get_hackathon_teams(
    hackathon_id: int,
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы")
):
    """
    Получение списка команд хакатона с пагинацией.
    
    Доступно всем пользователям.
    """
    # Рассчитываем смещение
    skip = (page - 1) * size
    
    # Получаем команды
    teams, total = await TeamRepository.get_hackathon_teams(hackathon_id, skip, size)
    
    # Рассчитываем общее количество страниц
    pages = (total + size - 1) // size if total > 0 else 1
    
    return PaginatedTeamsResponse(
        items=[TeamResponse.model_validate(t) for t in teams],
        total=total,
        page=page,
        size=size,
        pages=pages
    )




@router.post(
    "/{team_id}/members/{user_id}",
    response_model=dict,
    status_code=201,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Ошибка добавления участника"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        403: {"model": ErrorResponse, "description": "Недостаточно прав"},
        404: {"model": ErrorResponse, "description": "Команда не найдена"},
        500: {"model": ErrorResponse}
    }
)
async def add_team_member(
    team_id: int,
    user_id: int,
    current_user = Depends(get_current_user)
):
    """
    Добавление участника в команду.
    
    Доступно только капитану команды.
    Добавляемый пользователь должен быть зарегистрирован на хакатон.
    """
    try:
        # Проверяем, что текущий пользователь - капитан
        team = await TeamRepository.get_team_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Команда не найдена")
        
        if team.captain_id != current_user.id:
            raise HTTPException(status_code=403, detail="Только капитан может добавлять участников")
        
        await TeamRepository.add_team_member(team_id, user_id)
        return {"success": True, "message": "Участник добавлен в команду"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




@router.delete(
    "/{team_id}/members/{user_id}",
    response_model=dict,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Ошибка удаления участника"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        403: {"model": ErrorResponse, "description": "Недостаточно прав"},
        404: {"model": ErrorResponse, "description": "Участник не найден"},
        500: {"model": ErrorResponse}
    }
)
async def remove_team_member(
    team_id: int,
    user_id: int,
    current_user = Depends(get_current_user)
):
    """
    Удаление участника из команды.
    
    Доступно капитану или самому участнику.
    Капитан не может удалить себя из команды.
    """
    try:
        deleted = await TeamRepository.remove_team_member(team_id, user_id, current_user.id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Участник не найден")
        
        return {"success": True, "message": "Участник удален из команды"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




@router.post(
    "/{team_id}/invitations",
    response_model=TeamInvitationResponse,
    status_code=201,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Ошибка создания приглашения"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        403: {"model": ErrorResponse, "description": "Недостаточно прав"},
        404: {"model": ErrorResponse, "description": "Команда не найдена"},
        500: {"model": ErrorResponse}
    }
)
async def create_invitation(
    team_id: int,
    invitation_data: TeamInvitationCreate,
    current_user = Depends(get_current_user)
):
    """
    Создание приглашения в команду.
    
    Доступно только капитану команды.
    Приглашаемый пользователь должен быть зарегистрирован на хакатон.
    """
    try:
        invitation = await TeamRepository.create_invitation(invitation_data, current_user.id)
        
        # Получаем детальную информацию о приглашении
        from database import new_session
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        from models.team import TeamInvitationOrm, TeamOrm
        from models.user import UserOrm
        
        async with new_session() as session:
            query = (
                select(TeamInvitationOrm)
                .join(TeamOrm, TeamInvitationOrm.team_id == TeamOrm.id)
                .join(UserOrm, TeamInvitationOrm.inviter_id == UserOrm.id)
                .join(UserOrm, TeamInvitationOrm.invitee_id == UserOrm.id)
                .where(TeamInvitationOrm.id == invitation.id)
                .options(
                    selectinload(TeamInvitationOrm.team),
                    selectinload(TeamInvitationOrm.inviter),
                    selectinload(TeamInvitationOrm.invitee)
                )
            )
            
            result = await session.execute(query)
            detailed_invitation = result.scalars().first()
            
            if not detailed_invitation:
                raise HTTPException(status_code=404, detail="Приглашение не найдено")
            
            return TeamInvitationResponse.model_validate({
                'id': detailed_invitation.id,
                'team_id': detailed_invitation.team_id,
                'inviter_id': detailed_invitation.inviter_id,
                'invitee_id': detailed_invitation.invitee_id,
                'message': detailed_invitation.message,
                'status': detailed_invitation.status,
                'created_at': detailed_invitation.created_at,
                'updated_at': detailed_invitation.updated_at,
                'team_name': detailed_invitation.team.name,
                'inviter_telegram_username': detailed_invitation.inviter.telegram_username,
                'invitee_telegram_username': detailed_invitation.invitee.telegram_username
            })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




@router.patch(
    "/invitations/{invitation_id}",
    response_model=TeamInvitationResponse,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Ошибка обновления приглашения"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        403: {"model": ErrorResponse, "description": "Недостаточно прав"},
        404: {"model": ErrorResponse, "description": "Приглашение не найдено"},
        500: {"model": ErrorResponse}
    }
)
async def update_invitation(
    invitation_id: int,
    update_data: TeamInvitationUpdate,
    current_user = Depends(get_current_user)
):
    """
    Обновление статуса приглашения.
    
    Доступно только получателю приглашения.
    При принятии приглашения пользователь автоматически добавляется в команду.
    """
    try:
        invitation = await TeamRepository.update_invitation_status(
            invitation_id, 
            update_data, 
            current_user.id
        )
        
        if not invitation:
            raise HTTPException(status_code=404, detail="Приглашение не найдено")
        
        # Получаем детальную информацию
        from database import new_session
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        from models.team import TeamInvitationOrm, TeamOrm
        from models.user import UserOrm
        
        async with new_session() as session:
            query = (
                select(TeamInvitationOrm)
                .join(TeamOrm, TeamInvitationOrm.team_id == TeamOrm.id)
                .join(UserOrm, TeamInvitationOrm.inviter_id == UserOrm.id)
                .join(UserOrm, TeamInvitationOrm.invitee_id == UserOrm.id)
                .where(TeamInvitationOrm.id == invitation.id)
                .options(
                    selectinload(TeamInvitationOrm.team),
                    selectinload(TeamInvitationOrm.inviter),
                    selectinload(TeamInvitationOrm.invitee)
                )
            )
            
            result = await session.execute(query)
            detailed_invitation = result.scalars().first()
            
            if not detailed_invitation:
                raise HTTPException(status_code=404, detail="Приглашение не найдено")
            
            return TeamInvitationResponse.model_validate({
                'id': detailed_invitation.id,
                'team_id': detailed_invitation.team_id,
                'inviter_id': detailed_invitation.inviter_id,
                'invitee_id': detailed_invitation.invitee_id,
                'message': detailed_invitation.message,
                'status': detailed_invitation.status,
                'created_at': detailed_invitation.created_at,
                'updated_at': detailed_invitation.updated_at,
                'team_name': detailed_invitation.team.name,
                'inviter_telegram_username': detailed_invitation.inviter.telegram_username,
                'invitee_telegram_username': detailed_invitation.invitee.telegram_username
            })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




@router.get(
    "/invitations/my",
    response_model=List[TeamInvitationResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        500: {"model": ErrorResponse}
    }
)
async def get_my_invitations(
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    current_user = Depends(get_current_user)
):
    """
    Получение приглашений текущего пользователя.
    
    Доступно только авторизованным пользователям.
    """
    from models.team import InvitationStatus
    
    invitation_status = None
    if status:
        try:
            invitation_status = InvitationStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Некорректный статус")
    
    invitations = await TeamRepository.get_user_invitations(current_user.id, invitation_status)
    
    # Форматируем ответ
    formatted_invitations = []
    
    for invitation in invitations:
        from database import new_session
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        from models.team import TeamInvitationOrm, TeamOrm
        from models.user import UserOrm
        
        async with new_session() as session:
            query = (
                select(TeamInvitationOrm)
                .join(TeamOrm, TeamInvitationOrm.team_id == TeamOrm.id)
                .join(UserOrm, TeamInvitationOrm.inviter_id == UserOrm.id)
                .join(UserOrm, TeamInvitationOrm.invitee_id == UserOrm.id)
                .where(TeamInvitationOrm.id == invitation.id)
                .options(
                    selectinload(TeamInvitationOrm.team),
                    selectinload(TeamInvitationOrm.inviter),
                    selectinload(TeamInvitationOrm.invitee)
                )
            )
            
            result = await session.execute(query)
            detailed_invitation = result.scalars().first()
            
            if detailed_invitation:
                formatted_invitations.append({
                    'id': detailed_invitation.id,
                    'team_id': detailed_invitation.team_id,
                    'inviter_id': detailed_invitation.inviter_id,
                    'invitee_id': detailed_invitation.invitee_id,
                    'message': detailed_invitation.message,
                    'status': detailed_invitation.status,
                    'created_at': detailed_invitation.created_at,
                    'updated_at': detailed_invitation.updated_at,
                    'team_name': detailed_invitation.team.name,
                    'inviter_telegram_username': detailed_invitation.inviter.telegram_username,
                    'invitee_telegram_username': detailed_invitation.invitee.telegram_username
                })
    
    return [TeamInvitationResponse.model_validate(i) for i in formatted_invitations]




@router.get(
    "/users/search",
    response_model=PaginatedUsersResponse,
    responses={
        500: {"model": ErrorResponse}
    }
)
async def search_users(
    skills: Optional[str] = Query(None, description="Навыки через запятую"),
    search: Optional[str] = Query(None, description="Поиск по тексту"),
    position: Optional[str] = Query(None, description="Фильтр по позиции"),
    hackathon_id: Optional[int] = Query(None, description="Фильтр по хакатону"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы")
):
    """
    Поиск пользователей по фильтрам.
    
    Доступно всем пользователям.
    Можно фильтровать по навыкам, текстовому поиску, позиции и хакатону.
    """
    # Парсим навыки
    skills_list = None
    if skills:
        skills_list = [s.strip() for s in skills.split(',') if s.strip()]
    
    # Подготавливаем фильтры
    filters = UserSearchFilters(
        skills=skills_list,
        search=search,
        position=position
    )
    
    # Рассчитываем смещение
    skip = (page - 1) * size
    
    # Ищем пользователей
    users, total = await TeamRepository.search_users(filters, hackathon_id, skip, size)
    
    # Рассчитываем общее количество страниц
    pages = (total + size - 1) // size if total > 0 else 1
    
    return PaginatedUsersResponse(
        items=users,
        total=total,
        page=page,
        size=size,
        pages=pages
    )