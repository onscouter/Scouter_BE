from uuid import UUID
from fastapi import APIRouter, Depends, status, Request, Header, Response, HTTPException
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.auth import (
    verify_token,
    create_token,
    decode_token,
    create_refresh_token,
    set_refresh_token,
    clear_refresh_token,
)
from app.core.security import verify_password, hash_password
from app.db.init_db import get_db
from app.models import Employee, JobPosition
from app.models.core.job_position import PositionEnum
from app.rate_limiter import limiter
from limits.strategies import FixedWindowRateLimiter
from app.schemas.login import LoginPayload, AuthResponse
from app.schemas.employee import EmployeeOut, EmployeePut

router = APIRouter()

storage = limiter.limiter.storage
rate_limiter = FixedWindowRateLimiter(storage)


# ───────────────────────────────────────────────────────────────
@router.post("/refresh")
def refresh_token(request: Request, response: Response, db=Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        payload = decode_token(token)
        if payload.get("purpose") != "refresh":
            raise HTTPException(status_code=403, detail="Invalid token purpose")
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired refresh token")

    employee = db.query(Employee).filter_by(public_id=user_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="User not found")

    access_token = create_token(employee.public_id)
    return {"access_token": access_token}


@router.post("/logout")
def logout(response: Response):
    clear_refresh_token(response)
    return {"detail": "Logged out"}


# ───────────────────────────────────────────────────────────────
@router.get("/me", response_model=EmployeeOut)
def get_me(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    try:
        employee_id = UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token subject")

    employee = db.query(Employee).filter_by(public_id=employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="User not found")

    return EmployeeOut.model_validate(employee)


# ───────────────────────────────────────────────────────────────
@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
# @limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    data: LoginPayload,
    db: Session = Depends(get_db),
):
    employee = db.query(Employee).filter_by(username=data.username).first()

    if not employee:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.password, employee.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_token(employee.public_id)
    refresh_token = create_refresh_token(employee.public_id)
    set_refresh_token(response, refresh_token)

    return AuthResponse(
        access_token=access_token,
        employee=EmployeeOut.model_validate(employee)
    )


# ───────────────────────────────────────────────────────────────
@router.put("/signup", response_model=AuthResponse)
def signup(
    data: EmployeePut,
    onboarding_token: str = Header(..., alias="Onboarding-Token"),
    db: Session = Depends(get_db),
    response: Response = None
):
    payload = decode_token(onboarding_token)

    if payload.get("purpose") != "onboarding":
        raise HTTPException(status_code=403, detail="Invalid onboarding token")

    if payload.get("sub") != data.email:
        raise HTTPException(status_code=403, detail="Token/email mismatch")

    employee = db.query(Employee).filter_by(email=data.email).first()
    if not employee:
        raise HTTPException(status_code=404, detail="User not found")

    if employee.username and employee.password:
        raise HTTPException(status_code=400, detail="User already onboarded")

    if data.username:
        employee.username = data.username

    if data.password:
        employee.password = hash_password(data.password)

    if data.phone_number:
        employee.phone_number = data.phone_number.model_dump()

    job_data = data.job_position
    if job_data:
        new_job = JobPosition(
            title=job_data.title or "Untitled",
            status=job_data.status or PositionEnum.ACTIVE,
            description=job_data.description or "",
            company_id=employee.company_id,
        )
        db.add(new_job)
        db.flush()
        employee.job_position_id = new_job.id

    db.commit()
    db.refresh(employee)

    access_token = create_token(employee.public_id)
    refresh_token = create_refresh_token(employee.public_id)
    if response:
        set_refresh_token(response, refresh_token)

    return AuthResponse(
        access_token=access_token,
        employee=EmployeeOut.model_validate(employee)
    )
