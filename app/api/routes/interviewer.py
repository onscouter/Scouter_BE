from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc, func, distinct, literal
from sqlalchemy.orm import Session, joinedload

from app.core.auth import verify_token
from app.db.init_db import get_db
from app.models import (
    JobPosition,
    Company,
    Employee,
    JobApplication,
    Competency,
    JobInterview,
    Candidate,
)
from app.models.core.job_position import PositionEnum
from app.schemas.job_application import PaginatedApplicationResponse
from app.schemas.job_interview import PaginatedInterviewResponse, InterviewOut
from app.schemas.success_response import SuccessResponse

router = APIRouter()

# Config
ALLOWED_INTERVIEW_ORDER_FIELDS = {"candidate", "role", "competency", "interview_datetime"}
ALLOWED_ORDER_DIRS = {"asc", "desc"}
DEFAULT_ORDER_BY = "interview_datetime"
DEFAULT_ORDER_DIR = "desc"


@router.delete("/{interview_public_id}")
def delete_job(
        interview_public_id: str,
        payload: dict = Depends(verify_token),
        db: Session = Depends(get_db)
):
    employee_id = payload["sub"]
    employee = db.query(Employee).filter_by(public_id=employee_id).first()

    job = db.query(JobInterview).filter_by(public_id=interview_public_id).first()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {interview_public_id} not found")

    if not employee or employee.company_id != job.company_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to company data")

    db.delete(job)
    db.commit()

    return SuccessResponse(success=True, message=f"Job {interview_public_id} deleted")


@router.get("/interviews", response_model=PaginatedInterviewResponse)
def get_jobs(
        payload: dict = Depends(verify_token),
        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1),
        search: Optional[str] = Query(None),
        order_by: str = Query("interview_date"),
        order: str = Query("desc"),
        db: Session = Depends(get_db),
):
    # Validate auth
    employee = db.query(Employee).filter_by(public_id=payload["sub"]).first()
    print("filters", page, limit, order_by, order)
    if not employee:
        raise HTTPException(status_code=403, detail="Unauthorized access to company data")

    # Validate sorting inputs
    if order_by not in ALLOWED_INTERVIEW_ORDER_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid order_by field: {order_by}")
    if order not in ALLOWED_ORDER_DIRS:
        raise HTTPException(status_code=400, detail=f"Invalid order direction: {order}")

    # Build query
    query = (
        db.query(JobInterview)
        .filter(JobInterview.interviewer_id == employee.id)
        .options(
            joinedload(JobInterview.application)
            .joinedload(JobApplication.candidate),
            joinedload(JobInterview.application)
            .joinedload(JobApplication.job_position),
            joinedload(JobInterview.competency),
        )
    )

    # if job_status and job_status != "ALL":
    #     try:
    #         query = query.filter(JobPosition.status == PositionEnum(job_status).value)
    #     except ValueError:
    #         raise HTTPException(status_code=400, detail=f"Invalid job_status: {job_status}")

    if search:
        query = query.filter(JobPosition.title.ilike(f"%{search.lower()}%"))

    # Apply ordering
    order_field_map = {
        "candidate": func.concat(Candidate.first_name, Candidate.last_name),
        "role": JobPosition.title,
        "competency": Competency.name,
        "interview_datetime": JobInterview.interview_datetime,
    }
    order_column = order_field_map[order_by]
    query = query.order_by(asc(order_column) if order == "asc" else desc(order_column))

    # Pagination
    total = query.count()
    results = query.offset((page - 1) * limit).limit(limit).all()

    interviews = [
        InterviewOut(
            public_id=i.public_id,
            interview_datetime=i.interview_datetime,
            interview_status=i.interview_status,
            competency=i.competency,
            job_position=i.application.job_position,
            candidate=i.application.candidate,
        )
        for i in results
    ]
    return PaginatedInterviewResponse(
        interviews=interviews,
        total=total,
        page=page,
        limit=limit,
    )

# @router.get("/{interview_public_id}", response_model=PaginatedApplicationResponse)
# def get_applications_for_job_position(
#         job_position_public_id: UUID,
#         db: Session = Depends(get_db),
#         payload: dict = Depends(verify_token),
# ):
#   pass