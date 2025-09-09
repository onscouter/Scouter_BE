from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class CompanyBase(BaseModel):
    public_id: UUID = Field(alias="company_public_id")
    name: str
    is_active: bool

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class CompanyOut(CompanyBase):
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }
