from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc, func, text, distinct
from sqlalchemy.orm import Session

from app.core.auth import verify_token
from app.db.init_db import get_db
from app.models import JobPosition, Company, Employee, JobApplication, Competency
from app.models.core.job_position import PositionEnum
from app.schemas.job import PaginatedJobResponse, JobOut

router = APIRouter()

ALLOWED_ORDER_BY_FIELDS = {"title", "status", "created_at", "job_applications", "competencies"}
ALLOWED_ORDER_DIR = {"asc", "desc"}
ALLOWED_JOB_STATUSES = {"ACTIVE", "PAUSED", "COMPLETED"}


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
    auth0_id = payload["sub"]

    # Validate company and employee
    company = db.query(Company).filter_by(public_id=company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")

    employee = db.query(Employee).filter_by(auth0_id=auth0_id).first()
    if employee.company_id != company.id:
        raise HTTPException(status_code=403, detail="Employee not in company")

    if order_by not in ALLOWED_ORDER_BY_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid order_by field: {order_by}")
    if order not in ALLOWED_ORDER_DIR:
        raise HTTPException(status_code=400, detail=f"Invalid order direction: {order}")

    # Count labels
    job_app_count_label = func.count(distinct(JobApplication.id)).label("candidates")
    competency_count_label = func.count(distinct(Competency.id)).label("competencies")

    # Validate query params early
    if order_by not in ALLOWED_ORDER_BY_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid order_by field: {order_by}")
    if order not in ALLOWED_ORDER_DIR:
        raise HTTPException(status_code=400, detail=f"Invalid order direction: {order}")

    # Select fields
    base_query = (
        db.query(
            JobPosition.public_id,
            JobPosition.title,
            JobPosition.status,
            JobPosition.created_at,
            job_app_count_label,
            competency_count_label,
        )
        .filter(JobPosition.company_id == company.id)
        .outerjoin(JobPosition.job_applications)
        .outerjoin(JobPosition.competencies)
        .group_by(JobPosition.id)
    )

    # Optional filters
    if job_status and job_status != "ALL":
        try:
            job_status_enum = PositionEnum(job_status)
            base_query = base_query.filter(JobPosition.status == job_status_enum.value)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid job_status: {job_status}")

    if search:
        base_query = base_query.filter(JobPosition.title.ilike(f"%{search.lower()}%"))

    # Determine ordering field
    ORDER_FIELD_MAP = {
        "job_applications": job_app_count_label,
        "competencies": competency_count_label,
        "title": JobPosition.title,
        "status": JobPosition.status,
        "created_at": JobPosition.created_at,
    }

    order_field = ORDER_FIELD_MAP[order_by]
    base_query = base_query.order_by(asc(order_field) if order == "asc" else desc(order_field))

    # Pagination
    offset = (page - 1) * limit
    total = base_query.count()
    results = base_query.offset(offset).limit(limit).all()

    print(results)
    # Map results to response model
    jobs = [
        JobOut(
            public_id=public_id,
            title=title,
            status=status,
            created_at=created_at,
            job_applications=job_applications,
            competencies=competencies,
        )
        for (public_id, title, status, created_at, job_applications, competencies) in results
    ]

    return PaginatedJobResponse(
        jobs=jobs,
        total=total,
        page=page,
        limit=limit,
    )
