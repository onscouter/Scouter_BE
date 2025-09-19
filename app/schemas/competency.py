from typing import List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.rubric import Questions, RubricLevel


class CompetencyBase(BaseModel):
    name: str = Field(alias="competency_name")
    public_id: UUID = Field(alias="competency_public_id")
    description: str

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class CompetencyOut(CompetencyBase):
    rubric_levels: List[RubricLevel]
    questions: List[Questions]


class CompetencyMinimal(CompetencyBase):
    pass
