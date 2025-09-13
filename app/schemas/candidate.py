from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from app.schemas.phone_number import PhoneNumberOut
from pydantic import ConfigDict


class CandidateBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class CandidateOut(CandidateBase):
    public_id: UUID = Field(alias="candidate_public_id")
    phone_number: PhoneNumberOut

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class CandidateMinimal(CandidateBase):
    public_id: UUID = Field(alias="candidate_public_id")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
