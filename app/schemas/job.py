from uuid import UUID

from pydantic import BaseModel
from typing import List
from datetime import datetime
from app.models.core.job_position import PositionEnum


class JobOut(BaseModel):
    public_id: UUID
    title: str
    status: PositionEnum
    created_at: datetime
    job_applications: int
    competencies: int

    model_config = {"from_attributes": True}


class PaginatedJobResponse(BaseModel):
    jobs: List[JobOut]
    total: int
    page: int
    limit: int


class JobPositionMinimal(BaseModel):
    title: str

    model_config = {"from_attributes": True}
