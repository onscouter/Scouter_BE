from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from app.models.core.employee import RoleEnum
from .company import CompanyOut
from .job import JobPut
from .phone_number import PhoneNumberOut


class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    role: RoleEnum
    public_id: UUID = Field(alias="employee_public_id")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class EmployeePut(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    phone_number: Optional[PhoneNumberOut] = None
    job_position: Optional[JobPut] = None


# Full response
class EmployeeOut(EmployeeBase):
    username: str
    job_position_id: int
    phone_number: PhoneNumberOut
    company: CompanyOut
    created_at: datetime

    model_config = {"from_attributes": True}


# Minimal response
class EmployeeMinimal(BaseModel):
    public_id: UUID = Field(alias="employee_public_id")
    full_name: str

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }