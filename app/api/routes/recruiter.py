from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Form
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
    Candidate, PhoneNumber, InterviewStatusEnum,
)
from app.models.core.job_position import PositionEnum
from app.schemas.job import PaginatedJobResponse, JobOut
from app.schemas.job_application import PaginatedApplicationResponse, ApplicationOut
from app.schemas.success_response import SuccessResponse

router = APIRouter()

# Config
ALLOWED_JOB_ORDER_FIELDS = {"title", "status", "created_at", "job_applications", "competencies"}
ALLOWED_APP_ORDER_FIELDS = {"name", "created_at", "status"}
ALLOWED_ORDER_DIRS = {"asc", "desc"}
ALLOWED_JOB_STATUSES = {"ACTIVE", "PAUSED", "COMPLETED"}
DEFAULT_ORDER_BY = "created_at"
DEFAULT_ORDER_DIR = "desc"


@router.delete("/{job_id}")
def delete_job(
        job_id: str,
        payload: dict = Depends(verify_token),
        db: Session = Depends(get_db)
):
    employee_id = payload["sub"]
    employee = db.query(Employee).filter_by(public_id=employee_id).first()

    job = db.query(JobPosition).filter_by(public_id=job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if not employee or employee.company_id != job.company_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to company data")

    db.delete(job)
    db.commit()

    return SuccessResponse(success=True, message=f"Job {job_id} deleted")


@router.get("/jobs", response_model=PaginatedJobResponse)
def get_jobs(
        payload: dict = Depends(verify_token),
        company_id: str = Query(..., description="Public ID of the company"),
        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1),
        job_status: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        order_by: str = Query("title"),
        order: str = Query("desc"),
        db: Session = Depends(get_db),
):
    # Validate auth and ownership
    employee = db.query(Employee).filter_by(public_id=payload["sub"]).first()
    company = db.query(Company).filter_by(public_id=company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
    if not employee or employee.company_id != company.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to company data")

    # Validate sorting inputs
    if order_by not in ALLOWED_JOB_ORDER_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid order_by field: {order_by}")
    if order not in ALLOWED_ORDER_DIRS:
        raise HTTPException(status_code=400, detail=f"Invalid order direction: {order}")

    # Count labels
    job_app_count = func.count(distinct(JobApplication.id)).label("job_applications")
    competency_count = func.count(distinct(Competency.id)).label("competencies")

    # Build query
    query = (
        db.query(
            JobPosition.public_id,
            JobPosition.title,
            JobPosition.status,
            JobPosition.created_at,
            job_app_count,
            competency_count,
        )
        .filter(JobPosition.company_id == company.id)
        .outerjoin(JobPosition.job_applications)
        .outerjoin(JobPosition.competencies)
        .group_by(JobPosition.id)
    )

    if job_status and job_status != "ALL":
        try:
            query = query.filter(JobPosition.status == PositionEnum(job_status).value)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid job_status: {job_status}")

    if search:
        query = query.filter(JobPosition.title.ilike(f"%{search.lower()}%"))

    # Apply ordering
    order_field_map = {
        "title": JobPosition.title,
        "status": JobPosition.status,
        "created_at": JobPosition.created_at,
        "job_applications": job_app_count,
        "competencies": competency_count,
    }
    order_column = order_field_map[order_by]
    query = query.order_by(asc(order_column) if order == "asc" else desc(order_column))

    # Pagination
    total = query.count()
    results = query.offset((page - 1) * limit).limit(limit).all()

    return PaginatedJobResponse(
        jobs=[JobOut.model_validate(i) for i in results],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{job_position_public_id}", response_model=PaginatedApplicationResponse)
def get_applications_for_job_position(
        job_position_public_id: UUID,
        db: Session = Depends(get_db),
        payload: dict = Depends(verify_token),
        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1),
        search: Optional[str] = Query(None),
        order_by: str = Query(DEFAULT_ORDER_BY),
        order: str = Query(DEFAULT_ORDER_DIR),
):
    # Validate recruiter
    employee = db.query(Employee).filter_by(public_id=payload["sub"]).first()
    if not employee:
        raise HTTPException(status_code=403, detail="Recruiter not found")

    job_position = db.query(JobPosition).filter_by(public_id=job_position_public_id).first()
    if not job_position:
        raise HTTPException(status_code=404, detail="Job position not found")
    if job_position.company_id != employee.company_id:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    if order_by not in ALLOWED_APP_ORDER_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid order_by field: {order_by}")
    if order not in ALLOWED_ORDER_DIRS:
        raise HTTPException(status_code=400, detail=f"Invalid order direction: {order}")

    # Base query
    query = (
        db.query(JobApplication)
        .filter(JobApplication.job_position_id == job_position.id)
        .join(JobApplication.candidate)
        .options(
            joinedload(JobApplication.candidate),
            joinedload(JobApplication.interviews).joinedload(JobInterview.competency),
            joinedload(JobApplication.job_position),
        )
    )

    # Search
    if search:
        full_name = func.lower(func.concat(Candidate.first_name, literal(" "), Candidate.last_name))
        query = query.filter(
            full_name.ilike(f"%{search.lower()}%") |
            func.lower(Candidate.email).ilike(f"%{search.lower()}%")
        )

    # Ordering
    if order_by == "name":
        order_column = func.lower(func.concat(Candidate.first_name, literal(" "), Candidate.last_name))
    else:
        order_map = {
            "created_at": JobApplication.created_at,
            "status": JobApplication.status,
        }
        order_column = order_map[order_by]

    query = query.order_by(asc(order_column) if order == "asc" else desc(order_column))

    # Pagination
    total = query.count()
    apps = query.offset((page - 1) * limit).limit(limit).all()

    response = [
        ApplicationOut(
            public_id=app.public_id,
            candidate=app.candidate,
            created_at=app.created_at,
            interviews=app.interviews,
            status=app.status,
            job_position_title=app.job_position.title,
        )
        for app in apps
    ]

    return PaginatedApplicationResponse(
        applications=response,
        total=total,
        page=page,
        limit=limit,
    )

    # return PaginatedApplicationsResponse(
    #     applications=[ApplicationOut.model_validate(i) for i in apps],
    #     total=total,
    #     page=page,
    #     limit=limit,
    # )


@router.post("/{job_position_public_id}/new-candidate", response_model=SuccessResponse)
def create_candidate_for_job_position(
        job_position_public_id: UUID,
        db: Session = Depends(get_db),
        payload: dict = Depends(verify_token),
        first_name: str = Form(...),
        last_name: str = Form(...),
        email: str = Form(...),
        phone_number_raw: str = Form(...),
        phone_country_code: str = Form(...),
):
    employee = db.query(Employee).filter_by(public_id=payload["sub"]).first()
    if not employee:
        raise HTTPException(status_code=403, detail="Recruiter not found")

    job_position = db.query(JobPosition).filter_by(public_id=job_position_public_id).first()
    if not job_position:
        raise HTTPException(status_code=404, detail="Job position not found")

    if job_position.company_id != employee.company_id:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # existing_candidate = db.query(Candidate).filter_by(email=email).first()
    # if existing_candidate:
    #     raise HTTPException(status_code=400, detail="Candidate with this email already exists.")

    candidate = Candidate(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=PhoneNumber(number=phone_number_raw, country_code=phone_country_code)
    )
    db.add(candidate)
    db.flush()

    competencies = job_position.competencies

    application = JobApplication(
        candidate_id=candidate.id,
        job_position_id=job_position.id,
    )
    db.add(application)
    db.flush()

    for competency in competencies:
        interview = JobInterview(
            application_id=application.id,
            competency_id=competency.id,
            interview_status=InterviewStatusEnum.NOT_SCHEDULED,

        )
        db.add(interview)

    db.commit()

    return SuccessResponse(success=True, message=f"Candidate created: {candidate.public_id}")


@router.delete("/{job_position_id}/{candidate_id}")
def delete_candidate_from_job(
    job_position_id: str,
    candidate_id: str,
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    employee_id = payload["sub"]
    employee = db.query(Employee).filter_by(public_id=employee_id).first()

    if not employee:
        raise HTTPException(status_code=403, detail="Unauthorized")

    candidate = db.query(Candidate).filter_by(public_id=candidate_id).first()
    job_position = db.query(JobPosition).filter_by(public_id=job_position_id).first()

    if not candidate or not job_position:
        raise HTTPException(status_code=404, detail="Candidate or job not found")

    application = (
        db.query(JobApplication)
        .filter_by(candidate_id=candidate.id, job_position_id=job_position.id)
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Job application not found for this candidate and job",
        )

    db.query(JobInterview).filter_by(application_id=application.id).delete()

    db.delete(application)
    db.commit()

    return SuccessResponse(success=True, message="Candidate removed from job")
