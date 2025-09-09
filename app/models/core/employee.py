from __future__ import annotations

from enum import Enum
from typing import List

from sqlalchemy import ForeignKey, Integer, String, Enum as SqlEnum, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.abstract_base import AbstractBaseModel
from app.models.base import Base
from app.models.personal_base import AbstractPersonMixin


class RoleEnum(str, Enum):
    admin = "admin"
    recruiter = "recruiter"
    interviewer = "interviewer"


class Employee(AbstractBaseModel, AbstractPersonMixin, Base):
    __tablename__ = "employees"

    username: Mapped[str] = mapped_column(
        String(32),
        nullable=True,
        unique=True,
        index=True,
    )
    password: Mapped[str] = mapped_column(
        String(128),
        nullable=True
    )

    role: Mapped[RoleEnum] = mapped_column(
        SqlEnum(RoleEnum, name="role_enum", native_enum=False),
        nullable=False,
        default=RoleEnum.admin,
        server_default=text("'admin'"),
        index=True,
    )

    job_position_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("job_positions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    job_position: Mapped["JobPosition"] = relationship(
        "JobPosition", back_populates="employees", passive_deletes=True, lazy="selectin"
    )

    interviews: Mapped[List["JobInterview"]] = relationship(
        "JobInterview",
        back_populates="interviewer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    company: Mapped["Company"] = relationship(
        "Company", back_populates="employees", passive_deletes=True, lazy="selectin"
    )
