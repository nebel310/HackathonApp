from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field




class TeamMemberRole(str, Enum):
    """Роли участников команды."""
    CAPTAIN = 'captain'
    MEMBER = 'member'




class InvitationStatus(str, Enum):
    """Статусы приглашений в команду."""
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'




class TeamBase(BaseModel):
    """Базовая схема команды."""
    name: str = Field(..., min_length=1, max_length=200, example="Dream Team")
    description: Optional[str] = Field(None, example="Команда мечты для победы")
    hackathon_id: int = Field(..., example=1)




class TeamCreate(TeamBase):
    """Схема для создания команды."""
    pass




class TeamUpdate(BaseModel):
    """Схема для обновления команды (PATCH)."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, example="Новое название")
    description: Optional[str] = Field(None, example="Новое описание команды")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Обновленная команда",
                    "description": "Новое описание"
                }
            ]
        }
    )




class TeamMemberResponse(BaseModel):
    """Схема ответа с участником команды."""
    id: int
    user_id: int
    role: TeamMemberRole
    joined_at: datetime
    user_telegram_username: str = Field(..., example="john_doe")
    user_full_name: Optional[str] = Field(None, example="Иван Иванов")
    user_position: Optional[str] = Field(None, example="Бэкенд разработчик")
    
    model_config = ConfigDict(from_attributes=True)




class TeamResponse(TeamBase):
    """Схема ответа с информацией о команде."""
    id: int
    captain_id: int
    created_at: datetime
    updated_at: datetime
    members: List[TeamMemberResponse] = []
    captain_telegram_username: str = Field(..., example="john_doe")
    
    model_config = ConfigDict(from_attributes=True)




class TeamInvitationBase(BaseModel):
    """Базовая схема приглашения в команду."""
    team_id: int = Field(..., example=1)
    invitee_id: int = Field(..., example=2)
    message: Optional[str] = Field(None, example="Присоединяйся к нашей команде!")




class TeamInvitationCreate(TeamInvitationBase):
    """Схема для создания приглашения в команду."""
    pass




class TeamInvitationResponse(TeamInvitationBase):
    """Схема ответа с приглашением в команду."""
    id: int
    inviter_id: int
    status: InvitationStatus
    created_at: datetime
    updated_at: datetime
    team_name: str = Field(..., example="Dream Team")
    inviter_telegram_username: str = Field(..., example="john_doe")
    invitee_telegram_username: str = Field(..., example="jane_doe")
    
    model_config = ConfigDict(from_attributes=True)




class TeamInvitationUpdate(BaseModel):
    """Схема для обновления статуса приглашения."""
    status: InvitationStatus = Field(..., example="accepted")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "accepted"
                },
                {
                    "status": "rejected"
                }
            ]
        }
    )




class UserSearchFilters(BaseModel):
    """Схема фильтров для поиска пользователей."""
    skills: Optional[List[str]] = Field(None, example=["Python", "JavaScript"])
    search: Optional[str] = Field(None, example="Иван")
    position: Optional[str] = Field(None, example="Бэкенд")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "skills": ["Python", "FastAPI"],
                    "position": "разработчик"
                }
            ]
        }
    )




class PaginatedUsersResponse(BaseModel):
    """Схема ответа с пагинированным списком пользователей."""
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int




class PaginatedTeamsResponse(BaseModel):
    """Схема ответа с пагинированным списком команд."""
    items: List[TeamResponse]
    total: int
    page: int
    size: int
    pages: int