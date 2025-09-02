from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.models.base import Base
from app.models.abstract_base import AbstractBaseModel


class InterviewQuestion(AbstractBaseModel, Base):
    __tablename__ = "interview_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_text: Mapped[str] = mapped_column(String, nullable=False)

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
