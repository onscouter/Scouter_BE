from typing import List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.competency import CompetencyOut


class NewJobPayload(BaseModel):
    title: str
    description: str
    competencies: List[CompetencyOut]
