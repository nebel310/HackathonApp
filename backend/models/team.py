from datetime import datetime
from datetime import timezone
from enum import Enum as PyEnum

from sqlalchemy import ForeignKey
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import Integer
from sqlalchemy import Boolean
from sqlalchemy import Enum
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from database import Model




class TeamMemberRole(str, PyEnum):
    """Роли участников команды."""
    CAPTAIN = 'captain'
    MEMBER = 'member'




class InvitationStatus(str, PyEnum):
    """Статусы приглашений в команду."""
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'




class TeamOrm(Model):
    """Модель команды."""
    __tablename__ = 'teams'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey('hackathons.id', ondelete='CASCADE'))
    captain_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )




class TeamMemberOrm(Model):
    """Модель участника команды."""
    __tablename__ = 'team_members'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey('teams.id', ondelete='CASCADE'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    role: Mapped[TeamMemberRole] = mapped_column(
        Enum(TeamMemberRole, native_enum=False),
        default=TeamMemberRole.MEMBER
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )




class TeamInvitationOrm(Model):
    """Модель приглашения в команду."""
    __tablename__ = 'team_invitations'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey('teams.id', ondelete='CASCADE'))
    inviter_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    invitee_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus, native_enum=False),
        default=InvitationStatus.PENDING
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )