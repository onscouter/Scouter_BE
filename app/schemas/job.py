from uuid import UUID
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, conlist
from app.models.core.job_position import PositionEnum


class JobBase(BaseModel):
    title: str
    status: PositionEnum
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class JobOut(JobBase):
    public_id: UUID = Field(alias="job_position_public_id")
    created_at: datetime
    job_applications: int
    competencies: int

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class JobMinimal(JobBase):
    public_id: UUID = Field(alias="job_position_public_id")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class JobPut(BaseModel):
    title: Optional[str] = None
    status: Optional[PositionEnum] = None
    job_applications: Optional[int] = None
    competencies: Optional[conlist(UUID, min_length=1)] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedJobResponse(BaseModel):
    jobs: List[JobOut]
    total: int
    page: int
    limit: int
