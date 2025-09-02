from pydantic import BaseModel

from app.schemas.employee import EmployeeOut


class AccessGateOut(BaseModel):
    success: bool
    message: str = "Access verified"
    employee: EmployeeOut


class AccessGateRequest(BaseModel):
    access_code: str
