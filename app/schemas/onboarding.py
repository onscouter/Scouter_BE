from pydantic import BaseModel

from app.schemas.employee import EmployeeBase


class NeedsOnboardingOut(BaseModel):
    employee: EmployeeBase
    needs_onboarding: bool = False
