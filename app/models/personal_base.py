from sqlalchemy.orm import (
    declarative_mixin,
    Mapped,
    mapped_column,
    composite,
    declared_attr,
)
from sqlalchemy import String
from app.models.common import PhoneNumber


@declarative_mixin
class AbstractPersonMixin:
    __abstract__ = True

    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)

    email: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        index=True,
        nullable=False,
    )

    @declared_attr
    def phone_number(cls) -> Mapped[PhoneNumber]:
        return composite(
            PhoneNumber,
            mapped_column("phone_number_raw", String(20), nullable=False),
            mapped_column("phone_country_code", String(8), nullable=False),
        )

