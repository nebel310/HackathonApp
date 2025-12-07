from datetime import datetime
from typing import List, Optional, Dict, Any
import json

from pydantic import BaseModel, ConfigDict, Field, field_validator




class UserSkillBase(BaseModel):
    """Базовая схема навыка пользователя."""
    skill_name: str = Field(..., example="Python")




class UserSkillCreate(UserSkillBase):
    """Схема для создания навыка пользователя."""
    pass




class UserSkillResponse(UserSkillBase):
    """Схема ответа с навыком пользователя."""
    id: int
    user_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)




class UserBase(BaseModel):
    """Базовая схема пользователя."""
    telegram_username: str = Field(..., example="john_doe")
    full_name: Optional[str] = Field(None, example="Иван Иванов")
    position: Optional[str] = Field(None, example="Бэкенд разработчик")
    about: Optional[str] = Field(None, example="Люблю программировать")
    contacts: Optional[dict] = Field(
        None, 
        example={"email": "ivan@example.com", "telegram": "@ivanov"}
    )
    
    @field_validator('contacts', mode='before')
    @classmethod
    def parse_contacts(cls, v):
        """Парсит контакты из строки JSON."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v




class UserCreate(BaseModel):
    """Схема для создания пользователя."""
    telegram_username: str = Field(..., example="john_doe")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "telegram_username": "john_doe"
                }
            ]
        }
    )




class UserUpdate(BaseModel):
    """Схема для обновления пользователя (PATCH)."""
    full_name: Optional[str] = Field(None, example="Иван Иванов")
    position: Optional[str] = Field(None, example="Бэкенд разработчик")
    about: Optional[str] = Field(None, example="Люблю программировать")
    contacts: Optional[dict] = Field(
        None, 
        example={"email": "ivan@example.com", "telegram": "@ivanov"}
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "full_name": "Иван Иванов",
                    "position": "Бэкенд разработчик",
                    "about": "Люблю программировать",
                    "contacts": {"email": "ivan@example.com", "telegram": "@ivanov"}
                }
            ]
        }
    )




class UserResponse(BaseModel):
    """Схема ответа с информацией о пользователе."""
    id: int
    telegram_username: str
    role: str
    full_name: Optional[str] = None
    position: Optional[str] = None
    about: Optional[str] = None
    contacts: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    skills: List[UserSkillResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('contacts', mode='before')
    @classmethod
    def parse_contacts(cls, v):
        """Парсит контакты из строки JSON."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v




class UserWithTokenResponse(BaseModel):
    """Схема ответа с пользователем и токенами."""
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"




class TelegramLoginRequest(BaseModel):
    """Схема запроса входа через Telegram."""
    telegram_username: str = Field(..., example="john_doe")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "telegram_username": "john_doe"
                }
            ]
        }
    )




class TokenResponse(BaseModel):
    """Схема ответа с токенами."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer"
                }
            ]
        }
    )




class RefreshTokenRequest(BaseModel):
    """Схема запроса обновления токена."""
    refresh_token: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                }
            ]
        }
    )




class ErrorResponse(BaseModel):
    """Схема ответа для ошибок."""
    detail: str = Field(..., example="Сообщение об ошибке")




class ValidationErrorResponse(BaseModel):
    """Схема ответа для ошибок валидации."""
    detail: str = Field(..., example="Пользователь с таким именем уже существует")