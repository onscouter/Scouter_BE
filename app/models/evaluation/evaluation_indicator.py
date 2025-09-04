from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.models.abstract_base import AbstractBaseModel
from app.models.base import Base


class EvaluationIndicator(AbstractBaseModel, Base):
    __tablename__ = "evaluation_indicators"

    indicator_text: Mapped[str] = mapped_column(nullable=True)

    rubric_level_id: Mapped[int] = mapped_column(
        ForeignKey("competency_rubric_levels.id", ondelete="CASCADE"),
        nullable=False,
    )

    rubric_level: Mapped["CompetencyRubricLevel"] = relationship(
        "CompetencyRubricLevel",
        back_populates="indicators",
        lazy="selectin",
    )
