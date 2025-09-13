from typing import List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict
from app.schemas.candidate import CandidateOut
from app.schemas.job_interview import InterviewOut


class ApplicationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ApplicationOut(ApplicationBase):
    public_id: UUID = Field(alias="job_application_public_id")
    candidate: CandidateOut
    created_at: datetime
    interviews: List[InterviewOut]
    status: str
    job_position_title: str

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class PaginatedApplicationResponse(BaseModel):
    applications: List[ApplicationOut]
    total: int
    page: int
    limit: int
