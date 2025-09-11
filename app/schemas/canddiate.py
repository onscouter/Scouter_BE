from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.phone_number import PhoneNumberOut


class CandidateBase(BaseModel):

    model_config = {"from_attributes": True}


class CandidateOut(CandidateBase):
    public_id: UUID = Field(alias="candidate_public_id")
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: PhoneNumberOut

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }
