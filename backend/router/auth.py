from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from repositories.auth import AuthRepository
from repositories.user import UserRepository
from schemas.user import (
    ErrorResponse,
    ValidationErrorResponse,
    TelegramLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    UserWithTokenResponse
)
from utils.security import create_access_token
from utils.security import get_current_user
from utils.security import oauth2_scheme




router = APIRouter(
    prefix="/auth",
    tags=['Аутентификация']
)




@router.post(
    "/login",
    response_model=UserWithTokenResponse,
    status_code=200,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Ошибка аутентификации"},
        500: {"model": ErrorResponse}
    }
)
async def login_user(login_data: TelegramLoginRequest):
    """
    Вход в систему через Telegram username.
    
    Если пользователь с таким Telegram username не существует, он будет создан.
    Возвращает информацию о пользователе и JWT токены (access и refresh).
    """
    # Ищем пользователя
    user = await UserRepository.get_user_by_telegram_username(login_data.telegram_username)
    
    if not user:
        # Создаем нового пользователя
        from schemas.user import UserCreate
        user_data = UserCreate(telegram_username=login_data.telegram_username)
        user = await UserRepository.create_user(user_data)
    
    # Создаем токены
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = await AuthRepository.create_refresh_token(user.id)
    
    return UserWithTokenResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )




@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Неверный refresh токен"},
        500: {"model": ErrorResponse}
    }
)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """
    Обновление access токена с помощью refresh токена.
    
    Refresh токен должен быть валидным и не истекшим.
    Возвращает новый access токен и refresh токен.
    """
    user = await AuthRepository.get_user_by_refresh_token(refresh_data.refresh_token)
    
    if not user:
        raise HTTPException(status_code=400, detail="Неверный refresh токен")
    
    # Создаем новые токены
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = await AuthRepository.create_refresh_token(user.id)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )




@router.post(
    "/logout",
    response_model=dict,
    responses={
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        500: {"model": ErrorResponse}
    }
)
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user = Depends(get_current_user)
):
    """
    Выход из системы.
    
    Токен добавляется в черный список.
    Refresh токен пользователя отзывается.
    Требует валидный access токен.
    """
    await AuthRepository.add_to_blacklist(token)
    await AuthRepository.revoke_refresh_token(current_user.id)
    
    return {"success": True, "message": "Вы вышли из системы"}




@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        500: {"model": ErrorResponse}
    }
)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Получение информации о текущем пользователе.
    
    Возвращает данные пользователя из базы данных.
    Требует валидный access токен.
    """
    return UserResponse.model_validate(current_user)