from __future__ import annotations
from enum import Enum
from typing import List
from sqlalchemy import String, ForeignKey, Enum as SqlEnum, Integer, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations.recruitment import job_position_competency_mappings
from app.models.abstract_base import AbstractBaseModel
from app.models.base import Base


class PositionEnum(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class JobPosition(AbstractBaseModel, Base):
    __tablename__ = "job_positions"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[PositionEnum] = mapped_column(
        SqlEnum(PositionEnum, name="job_position_status_enum"),
        nullable=False,
        default=PositionEnum.ACTIVE,
        server_default=text("'ACTIVE'"),
        index=True,
    )
    description: Mapped[str] = mapped_column(String, nullable=False)

    company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company: Mapped["Company"] = relationship(
        "Company", back_populates="job_positions", passive_deletes=True
    )

    employees: Mapped[List["Employee"]] = relationship(
        "Employee",
        back_populates="job_position",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    job_applications: Mapped[List["JobApplication"]] = relationship(
        "JobApplication",
        back_populates="job_position",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    competencies: Mapped[List["Competency"]] = relationship(
        "Competency",
        secondary=job_position_competency_mappings,
        back_populates="job_positions",
        lazy="selectin",
    )
