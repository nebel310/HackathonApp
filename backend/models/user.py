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
from sqlalchemy.orm import relationship

from database import Model




class UserRole(str, PyEnum):
    """Роли пользователей в системе."""
    USER = "user"
    ADMIN = "admin"




class UserOrm(Model):
    """Модель пользователя в системе."""
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False),
        default=UserRole.USER
    )
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    position: Mapped[str | None] = mapped_column(String(100), nullable=True)
    about: Mapped[str | None] = mapped_column(Text, nullable=True)
    contacts: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON как текст
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Связь с навыками
    skills: Mapped[list["UserSkillOrm"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )




class UserSkillOrm(Model):
    """Модель навыков пользователя (теги)."""
    __tablename__ = 'user_skills'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    skill_name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Связь с пользователем
    user: Mapped["UserOrm"] = relationship(back_populates="skills")