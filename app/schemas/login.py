from pydantic import BaseModel

from app.schemas.employee import EmployeeOut


class LoginPayload(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    employee: EmployeeOut

    model_config = {
        "from_attributes": True
    }
