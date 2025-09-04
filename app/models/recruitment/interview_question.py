import enum

from sqlalchemy import String, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.models.base import Base
from app.models.abstract_base import AbstractBaseModel


class TypeLabel(str, enum.Enum):
    BEHAVIORAL = "BEHAVIORAL"
    TECHNICAL = "TECHNICAL"
    SITUATIONAL = "SITUATIONAL"


class InterviewQuestion(AbstractBaseModel, Base):
    __tablename__ = "interview_questions"

    question_text: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[TypeLabel] = mapped_column(
        SqlEnum(TypeLabel, name="question_type_enum"),
        nullable=False,
    )

    competency_id: Mapped[int] = mapped_column(
        ForeignKey("competencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    competency: Mapped["Competency"] = relationship(
        "Competency",
        back_populates="interview_questions",
        lazy="selectin",
    )
