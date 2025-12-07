from typing import List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from repositories.user import UserRepository
from schemas.user import (
    ErrorResponse,
    ValidationErrorResponse,
    UserResponse,
    UserUpdate,
    UserSkillCreate,
    UserSkillResponse
)
from utils.security import get_current_user




router = APIRouter(
    prefix="/profile",
    tags=['Профиль пользователя']
)




@router.get(
    "",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        500: {"model": ErrorResponse}
    }
)
async def get_profile(current_user = Depends(get_current_user)):
    """
    Получение профиля текущего пользователя.
    
    Возвращает полную информацию о пользователе, включая навыки.
    """
    return UserResponse.model_validate(current_user)




@router.patch(
    "",
    response_model=UserResponse,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Ошибка валидации"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        404: {"model": ErrorResponse, "description": "Пользователь не найден"},
        500: {"model": ErrorResponse}
    }
)
async def update_profile(
    update_data: UserUpdate,
    current_user = Depends(get_current_user)
):
    """
    Обновление профиля текущего пользователя.
    
    Поддерживает частичное обновление (PATCH).
    Можно обновить: ФИО, позицию, информацию о себе, контакты.
    """
    updated_user = await UserRepository.update_user(current_user.id, update_data)
    
    if not updated_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return UserResponse.model_validate(updated_user)




@router.get(
    "/skills",
    response_model=List[UserSkillResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        500: {"model": ErrorResponse}
    }
)
async def get_user_skills(current_user = Depends(get_current_user)):
    """
    Получение навыков текущего пользователя.
    
    Возвращает список всех навыков пользователя.
    """
    skills = await UserRepository.get_user_skills(current_user.id)
    return [UserSkillResponse.model_validate(skill) for skill in skills]




@router.post(
    "/skills",
    response_model=UserSkillResponse,
    status_code=201,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Навык уже существует"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        404: {"model": ErrorResponse, "description": "Пользователь не найден"},
        500: {"model": ErrorResponse}
    }
)
async def add_user_skill(
    skill_data: UserSkillCreate,
    current_user = Depends(get_current_user)
):
    """
    Добавление навыка текущему пользователю.
    
    Навык должен быть уникальным для пользователя.
    """
    skill = await UserRepository.add_user_skill(current_user.id, skill_data)
    
    if not skill:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return UserSkillResponse.model_validate(skill)




@router.delete(
    "/skills/{skill_id}",
    response_model=dict,
    responses={
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        404: {"model": ErrorResponse, "description": "Навык не найден"},
        500: {"model": ErrorResponse}
    }
)
async def delete_user_skill(
    skill_id: int,
    current_user = Depends(get_current_user)
):
    """
    Удаление навыка у текущего пользователя.
    
    Удаляет навык по его ID. Навык должен принадлежать текущему пользователю.
    """
    deleted = await UserRepository.remove_user_skill(current_user.id, skill_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Навык не найден")
    
    return {"success": True, "message": "Навык удален"}