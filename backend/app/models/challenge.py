from datetime import datetime, timezone
from enum import Enum
from typing import List
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Difficulty(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class ChallengeType(str, Enum):
    BUG_FIX = "BUG_FIX"
    FEATURE = "FEATURE"
    API = "API"
    DATABASE = "DATABASE"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    TESTING = "TESTING"
    CODE_REVIEW = "CODE_REVIEW"
    DEBUGGING = "DEBUGGING"


class Challenge(Base):
    __tablename__ = "challenges_challenge"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default=Difficulty.BEGINNER.value, nullable=False)
    challenge_type: Mapped[str] = mapped_column(String(20), default=ChallengeType.BUG_FIX.value, nullable=False)
    programming_language: Mapped[str] = mapped_column(String(50), default="Python", nullable=False)
    starter_code: Mapped[str] = mapped_column(Text, default="", nullable=False)
    entrypoint: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    time_limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    memory_limit: Mapped[int] = mapped_column(Integer, default=256, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    test_cases: Mapped[List["TestCase"]] = relationship(
        "TestCase",
        back_populates="challenge",
        cascade="all, delete-orphan",
        order_by="TestCase.id",
    )
    files: Mapped[List["ChallengeFile"]] = relationship(
        "ChallengeFile",
        back_populates="challenge",
        cascade="all, delete-orphan",
        order_by="ChallengeFile.path",
    )
    submissions: Mapped[List["Submission"]] = relationship(
        "Submission",
        back_populates="challenge",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Challenge(id={self.id}, title='{self.title}', difficulty='{self.difficulty}')>"


class TestCase(Base):
    __tablename__ = "challenges_testcase"
    __test__ = False  # Prevent pytest from treating TestCase model as a test suite

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    challenge_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("challenges_challenge.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    input_data: Mapped[str] = mapped_column(Text, default="", nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    challenge: Mapped["Challenge"] = relationship("Challenge", back_populates="test_cases")

    def __repr__(self) -> str:
        return f"<TestCase(id={self.id}, challenge_id={self.challenge_id}, name='{self.name}')>"


class ChallengeFile(Base):
    __tablename__ = "challenges_challengefile"
    __table_args__ = (
        UniqueConstraint("challenge_id", "path", name="challenges_challengefile_challenge_id_path_c5c8d203_uniq"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    challenge_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("challenges_challenge.id", ondelete="CASCADE"), nullable=False
    )
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_test: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_readonly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    challenge: Mapped["Challenge"] = relationship("Challenge", back_populates="files")

    def __repr__(self) -> str:
        return f"<ChallengeFile(id={self.id}, challenge_id={self.challenge_id}, path='{self.path}')>"
