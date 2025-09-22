from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.models.recruitment.job_interview import InterviewStatusEnum
from app.schemas.candidate import CandidateMinimal
from app.schemas.competency import CompetencyMinimal
from app.schemas.job import JobMinimal


class InterviewBase(BaseModel):
    competency: CompetencyMinimal
    interview_datetime: Optional[datetime] = None
    public_id: UUID = Field(alias="job_interview_public_id")
    interview_status: InterviewStatusEnum
    candidate: CandidateMinimal
    job_position: JobMinimal

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class InterviewOut(InterviewBase):
    score: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class InterviewWithMeta(BaseModel):
    interviewer_name: str
    interviewer_role: str
    total_interviews_conducted: int
    scheduled_at: str
    candidate: CandidateMinimal
    competency: CompetencyMinimal


class PaginatedInterviewResponse(BaseModel):
    interviews: List[InterviewOut]
    total: int
    page: int
    limit: int
