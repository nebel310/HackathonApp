from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field




class HackathonStatus(str, Enum):
    """Статусы хакатона."""
    REGISTRATION = 'registration'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'




class HackathonBase(BaseModel):
    """Базовая схема хакатона."""
    name: str = Field(..., min_length=1, max_length=200, example="Хакатон по AI")
    description: str = Field(..., min_length=1, example="Соревнование по созданию AI решений")
    start_date: datetime = Field(..., example="2024-01-15T10:00:00Z")
    end_date: datetime = Field(..., example="2024-01-17T18:00:00Z")
    status: HackathonStatus = Field(default=HackathonStatus.REGISTRATION, example="registration")
    min_team_size: int = Field(default=1, ge=1, example=2)
    max_team_size: int = Field(default=5, ge=1, example=4)




class HackathonCreate(HackathonBase):
    """Схема для создания хакатона."""
    pass




class HackathonUpdate(BaseModel):
    """Схема для обновления хакатона (PATCH)."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, example="Обновленное название")
    description: Optional[str] = Field(None, min_length=1, example="Обновленное описание")
    start_date: Optional[datetime] = Field(None, example="2024-01-20T10:00:00Z")
    end_date: Optional[datetime] = Field(None, example="2024-01-22T18:00:00Z")
    status: Optional[HackathonStatus] = Field(None, example="in_progress")
    min_team_size: Optional[int] = Field(None, ge=1, example=3)
    max_team_size: Optional[int] = Field(None, ge=1, example=5)
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Обновленное название хакатона",
                    "status": "in_progress"
                }
            ]
        }
    )




class HackathonResponse(HackathonBase):
    """Схема ответа с информацией о хакатоне."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)




class HackathonWithDetailsResponse(HackathonResponse):
    """Схема ответа с детальной информацией о хакатоне."""
    registration_count: int = Field(default=0, example=25)
    team_count: int = Field(default=0, example=5)




class HackathonSkillBase(BaseModel):
    """Базовая схема навыка хакатона."""
    skill_name: str = Field(..., min_length=1, max_length=50, example="Python")
    priority: int = Field(default=1, ge=1, le=10, example=1)




class HackathonSkillCreate(HackathonSkillBase):
    """Схема для создания навыка хакатона."""
    pass




class HackathonSkillResponse(HackathonSkillBase):
    """Схема ответа с навыком хакатона."""
    id: int
    hackathon_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)




class HackathonRegistrationBase(BaseModel):
    """Базовая схема регистрации на хакатон."""
    hackathon_id: int = Field(..., example=1)




class HackathonRegistrationCreate(HackathonRegistrationBase):
    """Схема для регистрации на хакатон."""
    pass




class HackathonRegistrationResponse(HackathonRegistrationBase):
    """Схема ответа с регистрацией на хакатон."""
    id: int
    user_id: int
    team_id: Optional[int] = None
    registration_date: datetime
    
    model_config = ConfigDict(from_attributes=True)




class PaginatedHackathonsResponse(BaseModel):
    """Схема ответа с пагинированным списком хакатонов."""
    items: List[HackathonResponse]
    total: int
    page: int
    size: int
    pages: int




class HackathonListFilters(BaseModel):
    """Схема фильтров для списка хакатонов."""
    status: Optional[HackathonStatus] = Field(None, example="registration")
    search: Optional[str] = Field(None, example="AI")
    start_date_from: Optional[datetime] = Field(None, example="2024-01-01T00:00:00Z")
    start_date_to: Optional[datetime] = Field(None, example="2024-12-31T23:59:59Z")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "registration",
                    "search": "AI"
                }
            ]
        }
    )