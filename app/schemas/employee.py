from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from app.models.core.employee import RoleEnum
from .company import CompanyOut
from .phone_number import PhoneNumberOut


# Shared fields
class EmployeeBase(BaseModel):
    full_name: str
    email: EmailStr
    role: RoleEnum
    public_id: UUID

    model_config = {"from_attributes": True}


# Full response
class EmployeeOut(EmployeeBase):
    job_position_id: int
    phone_number: PhoneNumberOut
    is_onboarding: bool
    auth0_id: str
    company: CompanyOut
    created_at: datetime

    model_config = {"from_attributes": True}


# Minimal response
class EmployeeMinimal(BaseModel):
    public_id: UUID
    full_name: str

    model_config = {"from_attributes": True}
