from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.recruitment.job_interview import InterviewStatusEnum
from app.schemas.competency import CompetencyMinimal


class InterviewBase(BaseModel):
    model_config = {"from_attributes": True}


# Full response
class InterviewOut(InterviewBase):
    competency: CompetencyMinimal
    interview_datetime: datetime
    public_id: UUID
    interview_status: InterviewStatusEnum
    score: Optional[int] = None
    model_config = {"from_attributes": True}
