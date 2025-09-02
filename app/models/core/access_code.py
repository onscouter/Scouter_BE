from __future__ import annotations

from sqlalchemy import String, ForeignKey, true, Boolean
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.models.abstract_base import AbstractBaseModel
from app.models.base import Base


class AccessCode(AbstractBaseModel, Base):
    __tablename__ = "access_codes"

    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true(), index=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    company: Mapped["Company"] = relationship(
        "Company", back_populates="access_codes", passive_deletes=True, lazy="selectin"
    )
