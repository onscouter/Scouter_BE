from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from app.models.core.employee import RoleEnum
from .candidate import CandidateMinimal
from .company import CompanyOut
from .competency import CompetencyMinimal
from .job import JobPut, JobMinimal
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
    job_position: JobMinimal
    phone_number: PhoneNumberOut
    company: CompanyOut
    created_at: datetime

    model_config = {"from_attributes": True}


# Minimal response
class EmployeeMinimal(BaseModel):
    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class EmployeeInterviewerOut(EmployeeOut):
    interview_count: int
    last_interviewed_at: Optional[str]

    model_config = {"from_attributes": True}


class PaginatedEmployeeResponse(BaseModel):
    employees: List[EmployeeInterviewerOut]
    candidate: CandidateMinimal
    competency: CompetencyMinimal
    total: int
    page: int
    limit: int
