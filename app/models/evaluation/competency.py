from typing import List

from sqlalchemy import String, Boolean
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.models.associations.recruitment import job_position_competency_mappings
from app.models.abstract_base import AbstractBaseModel
from app.models.base import Base


class Competency(AbstractBaseModel, Base):
    __tablename__ = "competencies"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )

    job_positions: Mapped[List["JobPosition"]] = relationship(
        "JobPosition",
        secondary=job_position_competency_mappings,
        back_populates="competencies",
        lazy="selectin",
    )

    interviews: Mapped[List["JobInterview"]] = relationship(
        "JobInterview",
        back_populates="competency",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    interview_questions: Mapped[List["InterviewQuestion"]] = relationship(
        "InterviewQuestion",
        back_populates="competency",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    rubric_levels: Mapped[List["CompetencyRubricLevel"]] = relationship(
        "CompetencyRubricLevel",
        back_populates="competency",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
