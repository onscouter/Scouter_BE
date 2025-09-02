from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.schemas.phone_number import PhoneNumberOut


class CandidateBase(BaseModel):

    model_config = {"from_attributes": True}


class CandidateOut(CandidateBase):
    public_id: UUID
    full_name: str
    email: EmailStr
    phone_number: PhoneNumberOut


    model_config = {"from_attributes": True}
