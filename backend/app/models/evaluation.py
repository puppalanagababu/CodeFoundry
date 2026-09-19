from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class EvaluationStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RequirementType(str, Enum):
    BUG_FIX_COUNT = "BUG_FIX_COUNT"
    SECURITY_COUNT = "SECURITY_COUNT"
    PERFORMANCE_COUNT = "PERFORMANCE_COUNT"
    TESTING_COUNT = "TESTING_COUNT"
    PERFECT_SCORE_COUNT = "PERFECT_SCORE_COUNT"
    TOTAL_COMPLETED_COUNT = "TOTAL_COMPLETED_COUNT"


class Evaluation(Base):
    __tablename__ = "evaluations_evaluation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("submissions_submission.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), default=EvaluationStatus.PENDING.value, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tests_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tests_passed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tests_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    memory_used: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    stdout: Mapped[str] = mapped_column(Text, default="", nullable=False)
    stderr: Mapped[str] = mapped_column(Text, default="", nullable=False)
    test_results: Mapped[List[Any]] = mapped_column(JSONB, default=list, nullable=False)
    skill_breakdown: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="evaluation")

    def __repr__(self) -> str:
        return f"<Evaluation(id={self.id}, submission_id={self.submission_id}, status='{self.status}', score={self.score})>"


class Achievement(Base):
    __tablename__ = "evaluations_achievement"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str] = mapped_column(String(50), default="🏆", nullable=False)
    requirement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    requirement_value: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user_achievements: Mapped[List["UserAchievement"]] = relationship(
        "UserAchievement",
        back_populates="achievement",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Achievement(id={self.id}, code='{self.code}', name='{self.name}')>"


class UserAchievement(Base):
    __tablename__ = "evaluations_userachievement"
    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="evaluations_userachievem_user_id_achievement_id_2816cf1a_uniq"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users_user.id", ondelete="CASCADE"), nullable=False
    )
    achievement_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("evaluations_achievement.id", ondelete="CASCADE"), nullable=False
    )
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="achievements")
    achievement: Mapped["Achievement"] = relationship("Achievement", back_populates="user_achievements")

    def __repr__(self) -> str:
        return f"<UserAchievement(id={self.id}, user_id={self.user_id}, achievement_id={self.achievement_id})>"
