from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserRole(str, Enum):
    STUDENT = "STUDENT"
    TRAINER = "TRAINER"
    ADMIN = "ADMIN"
    RECRUITER = "RECRUITER"


class User(Base):
    __tablename__ = "users_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(150), default="", nullable=False)
    last_name: Mapped[str] = mapped_column(String(150), default="", nullable=False)
    email: Mapped[str] = mapped_column(String(254), default="", nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    date_joined: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), default=UserRole.STUDENT.value, nullable=False)

    # Relationships
    submissions: Mapped[List["Submission"]] = relationship(
        "Submission",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(Submission.submitted_at)",
    )
    achievements: Mapped[List["UserAchievement"]] = relationship(
        "UserAchievement",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
