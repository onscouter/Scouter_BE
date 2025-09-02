from __future__ import annotations
import enum
from datetime import datetime, UTC
from typing import List

from sqlalchemy import ForeignKey, DateTime, Enum, Integer, text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.abstract_base import AbstractBaseModel
from app.models.base import Base


class JobApplicationStatus(str, enum.Enum):
    HIRE = "HIRE"
    PENDING = "PENDING"
    REJECT = "REJECT"


class JobApplication(AbstractBaseModel, Base):
    __tablename__ = "job_applications"

    # applied_on: Mapped[datetime] = mapped_column(
    #     DateTime(timezone=True),
    #     default=lambda: datetime.now(UTC),
    #     nullable=False,
    #     index=True,
    # )

    status: Mapped[JobApplicationStatus] = mapped_column(
        Enum(JobApplicationStatus, name="job_application_status_enum"),
        nullable=False,
        server_default=text("'PENDING'"),
        default=JobApplicationStatus.PENDING,
        index=True,
    )

    candidate_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_position_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("job_positions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    candidate: Mapped["Candidate"] = relationship(
        "Candidate",
        back_populates="job_applications",
        passive_deletes=True,
        lazy="selectin",
    )

    job_position: Mapped["JobPosition"] = relationship(
        "JobPosition",
        back_populates="job_applications",
        passive_deletes=True,
        lazy="selectin",
    )

    interviews: Mapped[List["JobInterview"]] = relationship(
        "JobInterview",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
