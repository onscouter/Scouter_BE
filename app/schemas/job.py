from uuid import UUID

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.core.job_position import PositionEnum


class JobOut(BaseModel):
    public_id: UUID = Field(alias="job_position_public_id")
    title: str
    status: PositionEnum
    created_at: datetime
    job_applications: int
    competencies: int

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class JobPut(BaseModel):
    title: Optional[str] = None
    status: Optional[PositionEnum] = None
    job_applications: Optional[int] = None
    competencies: Optional[List[UUID]] = None
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class PaginatedJobResponse(BaseModel):
    jobs: List[JobOut]
    total: int
    page: int
    limit: int


class JobPositionMinimal(BaseModel):
    title: str
    public_id: UUID = Field(alias="job_position_public_id")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }
