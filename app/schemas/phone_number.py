from pydantic import BaseModel


class PhoneNumberOut(BaseModel):
    number: str
    country_code: str

    model_config = {"from_attributes": True}