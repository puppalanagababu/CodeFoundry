from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SubmissionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"


class Submission(Base):
    __tablename__ = "submissions_submission"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users_user.id", ondelete="CASCADE"), nullable=False
    )
    challenge_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("challenges_challenge.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(Text, default="", nullable=False)
    files: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="Python", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=SubmissionStatus.PENDING.value, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    memory_used: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    test_results: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="submissions")
    challenge: Mapped["Challenge"] = relationship("Challenge", back_populates="submissions")
    evaluation: Mapped[Optional["Evaluation"]] = relationship(
        "Evaluation",
        back_populates="submission",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Submission(id={self.id}, user_id={self.user_id}, challenge_id={self.challenge_id}, status='{self.status}', score={self.score})>"
