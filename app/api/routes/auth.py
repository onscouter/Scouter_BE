from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status, Request
from app.core.auth import verify_token
from app.db.init_db import get_db
from sqlalchemy.orm import Session
from app.models import Employee, AccessCode
from fastapi import HTTPException
from typing import Union
from app.rate_limiter import limiter
from limits.util import parse_many
from limits.strategies import FixedWindowRateLimiter


from app.schemas.access_gate import AccessGateRequest, AccessGateOut
from app.schemas.employee import EmployeeOut, EmployeeBase
from app.schemas.onboarding import NeedsOnboardingOut

router = APIRouter()

storage = limiter.limiter.storage
rate_limiter = FixedWindowRateLimiter(storage)

# @router.get(
#     "/example",
#     response_model=ExampleOut,
#     status_code=status.HTTP_200_OK,
#     summary="Summary of what this does",
#     response_description="Successful response",
#     responses={404: {"description": "Not found"}},
# )
# def get_example(...):
#     """
#     Describe what the route does, who can call it, and edge cases.
#     """

# start with response_model, raise HTTPException


@router.get(
    "/me",
    response_model=EmployeeOut,
    status_code=status.HTTP_200_OK,
    summary="Get current logged-in employee info",
    response_description="Employee info for the current authenticated user",
    responses={
        404: {"description": "User not found"},
        401: {"description": "Not authenticated"},
    },
)
def get_me(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """
    Fetch the currently logged-in employee's profile using their Auth0 ID.
    """
    auth0_id = payload["sub"]

    employee = db.query(Employee).filter_by(auth0_id=auth0_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return employee


@router.get(
    "/login",
    response_model=Union[EmployeeOut, NeedsOnboardingOut],
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and check onboarding status",
    responses={
        404: {"description": "User not onboarded"},
        401: {"description": "Unauthorized"},
    },
)
@limiter.limit("5/minute")
def login(
        request: Request,
        payload: dict = Depends(verify_token),
        db: Session = Depends(get_db),
):
    auth0_id = payload["sub"]
    email = payload.get("email")

    employee = db.query(Employee).filter_by(auth0_id=auth0_id).first()
    if employee:
        print("employee")
        return EmployeeOut.model_validate(employee)

    if email:
        print("need verify")
        user_by_email = db.query(Employee).filter_by(email=email).first()
        if user_by_email:
            employee_base = EmployeeBase.model_validate(user_by_email)
            return NeedsOnboardingOut(employee=employee_base, needs_onboarding=True)

    raise HTTPException(status_code=404, detail="User not onboarded")


@router.post("/access-gate/verify", response_model=AccessGateOut)
@limiter.exempt
def verify_access_code(
        request: Request,
        data: AccessGateRequest,
        db: Session = Depends(get_db),
        payload: dict = Depends(verify_token),
):
    email = payload.get("email")
    auth0_id = payload["sub"]

    rate_limiter = FixedWindowRateLimiter(limiter.limiter.storage)
    limits = parse_many("5/minute;10/hour")
    for limit in limits:
        key = f"rate-limit:{auth0_id}"
        if not rate_limiter.hit(limit, key):
            raise HTTPException(status_code=429, detail="Too many access attempts.")

    employee = db.query(Employee).filter_by(email=email).first()
    if not employee:
        raise HTTPException(status_code=404, detail="User not found.")

    access_code = (
        db.query(AccessCode)
        .filter_by(
            code=data.access_code,
            role=employee.role,
            is_active=True,
            company_id=employee.company_id,
        )
        .first()
    )

    if not access_code:
        raise HTTPException(status_code=400, detail="Invalid or expired access code.")

    if employee.company_id != access_code.company_id:
        raise HTTPException(
            status_code=403, detail="Access code does not match user's company."
        )

    try:
        employee.auth0_id = auth0_id
        employee.is_onboarding = True
        db.commit()
        db.refresh(employee)
    except Exception as e:
        db.rollback()
        print("DB commit failed:", e)
        raise HTTPException(status_code=500, detail="Failed to update employee.")

    employee = EmployeeOut.model_validate(employee)

    return AccessGateOut(
        success=True,
        employee=employee
    )


@router.get("/access-gate/attempts")
@limiter.exempt
def get_attempts(request: Request, payload: dict = Depends(verify_token)):
    auth0_id = payload["sub"]

    storage = limiter.limiter.storage
    rate_limiter = FixedWindowRateLimiter(storage)

    limits = parse_many("5/minute;10/hour")
    attempt_info = []

    for limit in limits:
        key = f"rate-limit:{auth0_id}"  # ✅ Use your own key structure
        reset_ts, remaining = rate_limiter.get_window_stats(limit, key)
        reset_time = datetime.fromtimestamp(reset_ts, tz=timezone.utc).isoformat()

        attempt_info.append({
            "limit": str(limit),  # e.g., "5 per 1 minute"
            "remaining": remaining,
            "reset": reset_time
        })

    return {"employee": auth0_id, "limits": attempt_info}
