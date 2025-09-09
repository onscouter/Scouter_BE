from __future__ import annotations

from typing import List

from sqlalchemy import String, Boolean, true
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.models.base import Base
from app.models.abstract_base import AbstractBaseModel

import secrets, string


def generate_access_pin(length: int = 12) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Company(AbstractBaseModel, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true(), index=True
    )
    # access_pin: Mapped[str] = mapped_column(
    #     String(12), nullable=False, unique=True, default=generate_access_pin
    # )

    job_positions: Mapped[List["JobPosition"]] = relationship(
        "JobPosition",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    employees: Mapped[List["Employee"]] = relationship(
        "Employee",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

