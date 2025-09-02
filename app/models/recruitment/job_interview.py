from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer, DateTime, Enum as SqlEnum, text

from app.models.abstract_base import AbstractBaseModel
from app.models.base import Base


class InterviewStatusEnum(str, Enum):
    NOT_SCHEDULED = "NOT_SCHEDULED"  # No time has been set
    SCHEDULED = "SCHEDULED"  # Time has been set
    RESCHEDULED = "RESCHEDULED"  # Was scheduled but changed
    CANCELLED = "CANCELLED"  # Cancelled before occurring
    COMPLETED = "COMPLETED"  # Successfully happened
    NO_SHOW = "NO_SHOW"  # Candidate or interviewer didn’t show
    FEEDBACK_PENDING = "FEEDBACK_PENDING"  # Interview done but not yet graded


class JobInterview(AbstractBaseModel, Base):
    __tablename__ = "job_interviews"

    interview_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    interview_status: Mapped[InterviewStatusEnum] = mapped_column(
        SqlEnum(InterviewStatusEnum, name="interview_status_enum", create_type=True),
        nullable=False,
        default=InterviewStatusEnum.NOT_SCHEDULED,
        server_default=text("'NOT_SCHEDULED'"),
        index=True,
    )
    score: Mapped[int] = mapped_column(nullable=True)
    outcome: Mapped[str] = mapped_column(nullable=True)

    application_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interviewer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    competency_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("competencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    application: Mapped["JobApplication"] = relationship(
        "JobApplication", back_populates="interviews", lazy="selectin"
    )

    interviewer: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="interviews",
        lazy="selectin",
    )

    competency: Mapped["Competency"] = relationship(
        "Competency",
        back_populates="interviews",
        lazy="selectin",
    )
