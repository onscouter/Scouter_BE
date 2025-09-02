from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class CompanyBase(BaseModel):
    public_id: UUID
    name: str
    is_active: bool


class CompanyOut(CompanyBase):
    created_at: datetime

    model_config = {"from_attributes": True}
