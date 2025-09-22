from typing import List

from sqlalchemy import ForeignKey, Enum as SqlEnum, String, Integer
from sqlalchemy.orm import mapped_column, Mapped, relationship
import enum

from app.models.abstract_base import AbstractBaseModel
from app.models.base import Base


class RubricScoreLevel(int, enum.Enum):
    BELOW_EXPECTATIONS = 1
    MEETS_EXPECTATIONS = 2
    ABOVE_AVERAGE = 3
    EXCEEDS_EXPECTATIONS = 4
    OUTSTANDING = 5


class CompetencyRubricLevel(AbstractBaseModel, Base):
    __tablename__ = "competency_rubric_levels"

    level: Mapped[RubricScoreLevel] = mapped_column(
        SqlEnum(RubricScoreLevel, name="rubric_score_level_enum"), nullable=False
    )
    description: Mapped[str] = mapped_column(String, nullable=False)

    competency_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("competencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_position_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("job_positions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    indicators: Mapped[List["EvaluationIndicator"]] = relationship(
        "EvaluationIndicator",
        back_populates="rubric_level",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    competency: Mapped["Competency"] = relationship(
        "Competency",
        back_populates="rubric_levels",
        lazy="selectin",
    )

    job_position: Mapped["JobPosition"] = relationship(
        "JobPosition",
        back_populates="competency_rubric_levels",
        lazy="selectin"
    )
