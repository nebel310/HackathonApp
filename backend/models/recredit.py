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




class RecreditStatus(str, PyEnum):
    """Статусы заявок на перезачет."""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'




class RecreditRequestOrm(Model):
    """Модель заявки на перезачет."""
    __tablename__ = 'recredit_requests'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    hackathon_id: Mapped[int] = mapped_column(ForeignKey('hackathons.id', ondelete='CASCADE'))
    place_achieved: Mapped[int] = mapped_column(Integer, nullable=False)
    subject_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[RecreditStatus] = mapped_column(
        Enum(RecreditStatus, native_enum=False),
        default=RecreditStatus.PENDING
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )