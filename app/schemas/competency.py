from uuid import UUID

from pydantic import BaseModel


class CompetencyMinimal(BaseModel):
    name: str
    public_id: UUID

    model_config = {"from_attributes": True}
