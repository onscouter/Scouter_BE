from typing import List
from uuid import UUID

from pydantic import BaseModel
from datetime import datetime

from .canddiate import CandidateOut
from .job_interview import InterviewOut


# need to update the schemas to actually use the fields from the model

# Shared fields
class ApplicationBase(BaseModel):

    model_config = {"from_attributes": True}


# Full response
class ApplicationOut(ApplicationBase):
    public_id: UUID
    candidate: CandidateOut
    created_at: datetime
    interviews: List[InterviewOut]
    status: str
    job_position_title: str

    model_config = {"from_attributes": True}


class PaginatedApplicationsResponse(BaseModel):
    applications: List[ApplicationOut]
    total: int
    page: int
    limit: int

