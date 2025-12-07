from datetime import datetime
from datetime import timezone
from enum import Enum as PyEnum

from sqlalchemy import ForeignKey
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import Integer
from sqlalchemy import Enum
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from database import Model




class HackathonStatus(str, PyEnum):
    """Статусы хакатона."""
    REGISTRATION = 'registration'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'




class HackathonOrm(Model):
    """Модель хакатона."""
    __tablename__ = 'hackathons'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[HackathonStatus] = mapped_column(
        Enum(HackathonStatus, native_enum=False),
        default=HackathonStatus.REGISTRATION
    )
    min_team_size: Mapped[int] = mapped_column(Integer, default=1)
    max_team_size: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )




class HackathonRegistrationOrm(Model):
    """Модель регистрации пользователя на хакатон."""
    __tablename__ = 'hackathon_registrations'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey('hackathons.id', ondelete='CASCADE'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    registration_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey('teams.id', ondelete='SET NULL'),
        nullable=True
    )




class HackathonSkillOrm(Model):
    """Модель ключевых навыков для хакатона."""
    __tablename__ = 'hackathon_skills'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey('hackathons.id', ondelete='CASCADE'))
    skill_name: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )