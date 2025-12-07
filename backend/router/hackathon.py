from typing import List, Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status

from repositories.hackathon import HackathonRepository
from schemas.hackathon import (
    HackathonCreate,
    HackathonUpdate,
    HackathonResponse,
    HackathonWithDetailsResponse,
    HackathonListFilters,
    HackathonRegistrationCreate,
    HackathonRegistrationResponse,
    HackathonSkillCreate,
    HackathonSkillResponse,
    PaginatedHackathonsResponse,
    HackathonStatus
)
from schemas.user import ErrorResponse, ValidationErrorResponse
from utils.security import get_current_user, get_current_admin_user




router = APIRouter(
    prefix="/hackathons",
    tags=['Хакатоны']
)




@router.post(
    "",
    response_model=HackathonResponse,
    status_code=201,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Ошибка валидации"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        403: {"model": ErrorResponse, "description": "Недостаточно прав"},
        500: {"model": ErrorResponse}
    }
)
async def create_hackathon(
    hackathon_data: HackathonCreate,
    current_user = Depends(get_current_admin_user)
):
    """
    Создание нового хакатона.
    
    Доступно только администраторам.
    """
    hackathon = await HackathonRepository.create_hackathon(hackathon_data)
    return HackathonResponse.model_validate(hackathon)




@router.get(
    "",
    response_model=PaginatedHackathonsResponse,
    responses={
        500: {"model": ErrorResponse}
    }
)
async def get_hackathons(
    status: Optional[HackathonStatus] = Query(None, description="Фильтр по статусу"),
    search: Optional[str] = Query(None, description="Поиск по названию и описанию"),
    start_date_from: Optional[str] = Query(None, description="Дата начала от"),
    start_date_to: Optional[str] = Query(None, description="Дата начала до"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы")
):
    """
    Получение списка хакатонов с пагинацией и фильтрами.
    
    Доступно всем пользователям.
    """
    # Подготавливаем фильтры
    filters = HackathonListFilters(
        status=status,
        search=search,
        start_date_from=start_date_from,
        start_date_to=start_date_to
    )
    
    # Рассчитываем смещение
    skip = (page - 1) * size
    
    # Получаем хакатоны
    hackathons, total = await HackathonRepository.get_hackathons(filters, skip, size)
    
    # Рассчитываем общее количество страниц
    pages = (total + size - 1) // size if total > 0 else 1
    
    return PaginatedHackathonsResponse(
        items=[HackathonResponse.model_validate(h) for h in hackathons],
        total=total,
        page=page,
        size=size,
        pages=pages
    )




@router.get(
    "/{hackathon_id}",
    response_model=HackathonWithDetailsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Хакатон не найден"},
        500: {"model": ErrorResponse}
    }
)
async def get_hackathon(hackathon_id: int):
    """
    Получение информации о хакатоне.
    
    Доступно всем пользователям.
    """
    result = await HackathonRepository.get_hackathon_with_details(hackathon_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Хакатон не найден")
    
    hackathon, registration_count, team_count = result
    
    response = HackathonWithDetailsResponse.model_validate(hackathon)
    response.registration_count = registration_count
    response.team_count = team_count
    
    return response




@router.patch(
    "/{hackathon_id}",
    response_model=HackathonResponse,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Ошибка валидации"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        403: {"model": ErrorResponse, "description": "Недостаточно прав"},
        404: {"model": ErrorResponse, "description": "Хакатон не найден"},
        500: {"model": ErrorResponse}
    }
)
async def update_hackathon(
    hackathon_id: int,
    update_data: HackathonUpdate,
    current_user = Depends(get_current_admin_user)
):
    """
    Обновление хакатона.
    
    Доступно только администраторам.
    Поддерживает частичное обновление (PATCH).
    """
    updated_hackathon = await HackathonRepository.update_hackathon(hackathon_id, update_data)
    
    if not updated_hackathon:
        raise HTTPException(status_code=404, detail="Хакатон не найден")
    
    return HackathonResponse.model_validate(updated_hackathon)




@router.delete(
    "/{hackathon_id}",
    response_model=dict,
    responses={
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        403: {"model": ErrorResponse, "description": "Недостаточно прав"},
        404: {"model": ErrorResponse, "description": "Хакатон не найден"},
        500: {"model": ErrorResponse}
    }
)
async def delete_hackathon(
    hackathon_id: int,
    current_user = Depends(get_current_admin_user)
):
    """
    Удаление хакатона.
    
    Доступно только администраторам.
    """
    deleted = await HackathonRepository.delete_hackathon(hackathon_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Хакатон не найден")
    
    return {"success": True, "message": "Хакатон удален"}




@router.post(
    "/{hackathon_id}/register",
    response_model=HackathonRegistrationResponse,
    status_code=201,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Ошибка регистрации"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        404: {"model": ErrorResponse, "description": "Хакатон не найден"},
        500: {"model": ErrorResponse}
    }
)
async def register_for_hackathon(
    hackathon_id: int,
    registration_data: HackathonRegistrationCreate,
    current_user = Depends(get_current_user)
):
    """
    Регистрация на хакатон.
    
    Доступно только авторизованным пользователям.
    Регистрация возможна только если хакатон в статусе 'registration'.
    """
    try:
        registration = await HackathonRepository.register_for_hackathon(
            hackathon_id, 
            current_user.id
        )
        return HackathonRegistrationResponse.model_validate(registration)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




@router.delete(
    "/{hackathon_id}/register",
    response_model=dict,
    responses={
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        404: {"model": ErrorResponse, "description": "Регистрация не найдена"},
        500: {"model": ErrorResponse}
    }
)
async def unregister_from_hackathon(
    hackathon_id: int,
    current_user = Depends(get_current_user)
):
    """
    Отмена регистрации на хакатон.
    
    Доступно только авторизованным пользователям.
    """
    unregistered = await HackathonRepository.unregister_from_hackathon(
        hackathon_id, 
        current_user.id
    )
    
    if not unregistered:
        raise HTTPException(status_code=404, detail="Регистрация не найдена")
    
    return {"success": True, "message": "Регистрация отменена"}




@router.get(
    "/my/registrations",
    response_model=List[HackathonRegistrationResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        500: {"model": ErrorResponse}
    }
)
async def get_my_hackathon_registrations(current_user = Depends(get_current_user)):
    """
    Получение списка хакатонов, на которые зарегистрирован текущий пользователь.
    
    Доступно только авторизованным пользователям.
    """
    registrations = await HackathonRepository.get_user_hackathon_registrations(current_user.id)
    return [HackathonRegistrationResponse.model_validate(r) for r in registrations]




@router.post(
    "/{hackathon_id}/skills",
    response_model=HackathonSkillResponse,
    status_code=201,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Навык уже существует"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        403: {"model": ErrorResponse, "description": "Недостаточно прав"},
        404: {"model": ErrorResponse, "description": "Хакатон не найден"},
        500: {"model": ErrorResponse}
    }
)
async def add_hackathon_skill(
    hackathon_id: int,
    skill_data: HackathonSkillCreate,
    current_user = Depends(get_current_admin_user)
):
    """
    Добавление ключевого навыка для хакатона.
    
    Доступно только администраторам.
    Навык должен быть уникальным для хакатона.
    """
    try:
        skill = await HackathonRepository.add_hackathon_skill(hackathon_id, skill_data)
        
        if not skill:
            raise HTTPException(status_code=404, detail="Хакатон не найден")
        
        return HackathonSkillResponse.model_validate(skill)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




@router.get(
    "/{hackathon_id}/skills",
    response_model=List[HackathonSkillResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Хакатон не найден"},
        500: {"model": ErrorResponse}
    }
)
async def get_hackathon_skills(hackathon_id: int):
    """
    Получение ключевых навыков хакатона.
    
    Доступно всем пользователям.
    """
    # Проверяем существование хакатона
    hackathon = await HackathonRepository.get_hackathon_by_id(hackathon_id)
    if not hackathon:
        raise HTTPException(status_code=404, detail="Хакатон не найден")
    
    skills = await HackathonRepository.get_hackathon_skills(hackathon_id)
    return [HackathonSkillResponse.model_validate(s) for s in skills]




@router.delete(
    "/{hackathon_id}/skills/{skill_id}",
    response_model=dict,
    responses={
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        403: {"model": ErrorResponse, "description": "Недостаточно прав"},
        404: {"model": ErrorResponse, "description": "Навык не найден"},
        500: {"model": ErrorResponse}
    }
)
async def delete_hackathon_skill(
    hackathon_id: int,
    skill_id: int,
    current_user = Depends(get_current_admin_user)
):
    """
    Удаление ключевого навыка хакатона.
    
    Доступно только администраторам.
    """
    deleted = await HackathonRepository.remove_hackathon_skill(hackathon_id, skill_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Навык не найден")
    
    return {"success": True, "message": "Навык удален"}