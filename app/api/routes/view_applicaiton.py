from uuid import UUID

from fastapi import Query, Depends, HTTPException, APIRouter
from sqlalchemy import asc, desc
from sqlalchemy.orm import joinedload, Session
from sqlalchemy.sql import func
from typing import List, Optional

from app.core.auth import verify_token
from app.db.init_db import get_db
from app.models import Employee, JobPosition, JobApplication, JobInterview, Candidate
from app.schemas.job_application import PaginatedApplicationsResponse, ApplicationOut

ALLOWED_ORDER_BY_FIELDS = {"full_name", "created_at", "status"}
ALLOWED_ORDER_DIR = {"asc", "desc"}

router = APIRouter()


@router.get("/{public_id}", response_model=PaginatedApplicationsResponse)
def get_applications_for_job_position(
        public_id: UUID,
        db: Session = Depends(get_db),
        payload: dict = Depends(verify_token),
        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1),
        search: Optional[str] = Query(None),
        order_by: str = Query("created_at"),
        order: str = Query("desc"),
):

    auth0_id = payload["sub"]
    recruiter = db.query(Employee).filter_by(auth0_id=auth0_id).first()
    if not recruiter:
        raise HTTPException(status_code=403, detail="Recruiter not found")

    job_position = db.query(JobPosition).filter_by(public_id=public_id).first()
    if not job_position:
        raise HTTPException(status_code=404, detail="Job position not found")

    if job_position.company_id != recruiter.company_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this job")

    if order_by not in ALLOWED_ORDER_BY_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid order_by field: {order_by}")
    if order not in ALLOWED_ORDER_DIR:
        raise HTTPException(status_code=400, detail=f"Invalid order direction: {order}")

    # Base query with joins
    base_query = (
        db.query(JobApplication)
        .filter(JobApplication.job_position_id == job_position.id)
        .join(JobApplication.candidate)
        .options(
            joinedload(JobApplication.candidate),
            joinedload(JobApplication.interviews).joinedload(JobInterview.competency),
            joinedload(JobApplication.job_position),
        )
    )

    # Search by candidate name or email
    if search:
        base_query = base_query.filter(
            func.lower(Candidate.full_name).ilike(f"%{search.lower()}%") |
            func.lower(Candidate.email).ilike(f"%{search.lower()}%")
        )

    # Ordering
    ORDER_MAP = {
        "full_name": Candidate.full_name,
        "created_at": JobApplication.created_at,
        "status": JobApplication.status,
    }
    order_column = ORDER_MAP[order_by]
    base_query = base_query.order_by(asc(order_column) if order == "asc" else desc(order_column))

    # Pagination
    offset = (page - 1) * limit
    total = base_query.count()
    applications = base_query.offset(offset).limit(limit).all()

    response = [
        ApplicationOut(
            public_id=app.public_id,
            candidate=app.candidate,
            created_at=app.created_at,
            interviews=app.interviews,
            status=app.status,
            job_position_title=app.job_position.title,
        )
        for app in applications
    ]

    return PaginatedApplicationsResponse(
        applications=response,
        total=total,
        page=page,
        limit=limit,
    )
