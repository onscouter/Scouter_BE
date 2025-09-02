from __future__ import annotations

from typing import List

from sqlalchemy.orm import Mapped, relationship

from app.models.abstract_base import AbstractBaseModel
from app.models.base import Base
from app.models.personal_base import AbstractPersonMixin


class Candidate(AbstractBaseModel, AbstractPersonMixin, Base):
    __tablename__ = "candidates"

    job_applications: Mapped[List["JobApplication"]] = relationship(
        "JobApplication",
        back_populates="candidate",
        passive_deletes=True,
        lazy="selectin",
    )
