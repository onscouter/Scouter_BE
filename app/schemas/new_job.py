from pydantic import BaseModel
from typing import List


class Indicator(BaseModel):
    competencyId: str
    text: str


class EvaluationCriterion(BaseModel):
    score: int
    description: str
    indicators: List[Indicator]


class InterviewQuestion(BaseModel):
    id: str
    text: str
    type: str


class RubricBlock(BaseModel):
    competencyId: str
    competencyName: str
    description: str
    criteria: List[EvaluationCriterion]
    questions: List[InterviewQuestion]


class NewJobPayload(BaseModel):
    title: str
    description: str
    rubric: List[RubricBlock]
