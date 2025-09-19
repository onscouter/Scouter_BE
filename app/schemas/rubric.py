from typing import List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class Questions(BaseModel):
    public_id: UUID = Field(alias="interview_question_public_id")
    text: str = Field(alias="question_text")
    type: str

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class Indicator(BaseModel):
    public_id: UUID = Field(alias="evaluation_indicator_public_id")
    indicator_text: str

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class RubricLevel(BaseModel):
    public_id: UUID = Field(alias="rubric_level_public_id")
    level: int
    description: str
    indicators: List[Indicator]

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
