from sqlalchemy import ForeignKey, Enum
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


class RubricLabel(str, enum.Enum):
    BELOW = "Below Expectations"
    MEETS = "Meets Expectations"
    ABOVE = "Above Average"
    EXCEEDS = "Exceeds Expectations"
    OUTSTANDING = "Outstanding"


class CompetencyRubricLevel(AbstractBaseModel, Base):
    __tablename__ = "competency_rubric_levels"

    id: Mapped[int] = mapped_column(primary_key=True)
    competency_id: Mapped[int] = mapped_column(
        ForeignKey("competencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    level: Mapped[RubricScoreLevel] = mapped_column(
        Enum(RubricScoreLevel, name="rubric_score_level_enum"), nullable=False
    )
    label: Mapped[RubricLabel] = mapped_column(
        Enum(RubricLabel, name="rubric_label_enum"), nullable=False
    )
    description: Mapped[str] = mapped_column(nullable=True)
    key_indicators: Mapped[str] = mapped_column(nullable=True)

    competency: Mapped["Competency"] = relationship(
        "Competency",
        back_populates="rubric_levels",
        lazy="selectin",
    )
