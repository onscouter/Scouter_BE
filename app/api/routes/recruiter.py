from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Form, Path
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
from app.models.core import RoleEnum
from app.models.core.job_position import PositionEnum, JobType
from app.schemas.candidate import CandidateMinimal, CandidateOut
from app.schemas.competency import CompetencyMinimal
from app.schemas.job import PaginatedJobResponse, JobOut, JobMinimal
from app.schemas.job_application import PaginatedApplicationResponse, ApplicationOut
from app.schemas.job_interview import InterviewWithMeta, InterviewOut
from app.schemas.phone_number import PhoneNumberOut
from app.schemas.success_response import SuccessResponse
from app.schemas.employee import PaginatedEmployeeResponse, EmployeeInterviewerOut, EmployeeOut

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
        company_public_id: str = Query(..., description="Public ID of the company"),
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
    company = db.query(Company).filter_by(public_id=company_public_id).first()

    if not company:
        raise HTTPException(status_code=404, detail=f"Company {company_public_id} not found")
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
            JobPosition.description,
            job_app_count,
            competency_count,
        )
        .filter(JobPosition.company_id == company.id,
                JobPosition.job_type == JobType.EXTERNAL
                )
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


@router.get("/interviewer-meta/{job_interview_public_id}", response_model=InterviewWithMeta)
def get_candidate_interview(
        job_interview_public_id: str = Path(...),
        db: Session = Depends(get_db),
        payload: dict = Depends(verify_token),
):
    recruiter = db.query(Employee).filter_by(public_id=payload["sub"]).first()
    if not recruiter:
        raise HTTPException(status_code=403, detail="Recruiter not found")

    job_interview = db.query(JobInterview).filter_by(public_id=job_interview_public_id).first()
    if not job_interview:
        raise HTTPException(status_code=404, detail="Job interview not found")

    interviewer = db.query(Employee).filter_by(id=job_interview.interviewer_id).first()
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found")

    total_interviews = (
        db.query(JobInterview)
        .filter_by(interviewer_id=interviewer.id)
        .count()
    )

    application = db.query(JobApplication).filter_by(id=job_interview.application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Job application not found")

    candidate = db.query(Candidate).filter_by(id=application.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    competency = db.query(Competency).filter_by(id=job_interview.competency_id).first()
    if not competency:
        raise HTTPException(status_code=404, detail="Competency not found")

    full_name = interviewer.first_name + " " + interviewer.last_name

    return InterviewWithMeta(
        interviewer_name=full_name,
        interviewer_role=interviewer.role,
        total_interviews_conducted=total_interviews,
        scheduled_at=job_interview.interview_datetime.isoformat(),
        candidate=CandidateMinimal.model_validate(candidate),
        competency=CompetencyMinimal.model_validate(competency),
    )


@router.put("/{job_interview_public_id}/add-interviewer", response_model=SuccessResponse)
def add_interview(
        job_interview_public_id: str = Path(...),
        employee_public_id: str = Query(...),
        date_time: str = Query(...),
        db: Session = Depends(get_db),
        payload: dict = Depends(verify_token),
):
    recruiter = db.query(Employee).filter_by(public_id=payload["sub"]).first()
    if not recruiter:
        raise HTTPException(status_code=403, detail="Recruiter not found")

    interviewer = db.query(Employee).filter_by(public_id=employee_public_id).first()
    if not interviewer:
        raise HTTPException(status_code=403, detail="Interviewer not found")

    job_interview = db.query(JobInterview).filter_by(public_id=job_interview_public_id).first()
    if not job_interview:
        raise HTTPException(status_code=404, detail="Job interview not found or unauthorized")

    try:
        interview_dt = datetime.fromisoformat(date_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO 8601.")
    print("here", interview_dt, interviewer.id)
    job_interview.interviewer_id = interviewer.id
    job_interview.interview_datetime = interview_dt
    job_interview.interview_status = InterviewStatusEnum.SCHEDULED
    db.commit()

    return SuccessResponse(
        success=True,
        message=f"Interviewer {interviewer.public_id} added to interview {job_interview_public_id}",
    )


@router.get("/get-interviewers", response_model=PaginatedEmployeeResponse)
def get_interviewers(
        job_position_public_id: str = Query(...),
        job_interview_public_id: str = Query(...),
        job_application_public_id: str = Query(...),

        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1),
        db: Session = Depends(get_db),
        payload: dict = Depends(verify_token),
):

    employee = db.query(Employee).filter_by(public_id=payload["sub"]).first()
    if not employee:
        raise HTTPException(status_code=403, detail="Recruiter not found")

    job_position = db.query(JobPosition).filter_by(public_id=job_position_public_id).first()
    if not job_position or job_position.company_id != employee.company_id:
        raise HTTPException(status_code=404, detail="Job position not found or unauthorized")

    job_interview = db.query(JobInterview).filter_by(public_id=job_interview_public_id).first()
    if not job_interview:
        raise HTTPException(status_code=404, detail="Job interview not found or unauthorized")

    job_application = db.query(JobApplication).filter_by(public_id=job_application_public_id).first()
    if not job_application or job_interview.application_id != job_application.id:
        raise HTTPException(status_code=404, detail="Job interview unauthorized")

    competency = db.query(Competency).filter_by(id=job_interview.competency_id).first()
    candidate = db.query(Candidate).filter_by(id=job_application.candidate_id).first()

    interview_stats_subq = (
        db.query(
            JobInterview.interviewer_id.label("interviewer_id"),
            func.count().label("interview_count"),
            func.max(JobInterview.interview_datetime).label("last_interviewed_at")
        )
        .group_by(JobInterview.interviewer_id)
        .subquery()
    )

    query = (
        db.query(
            Employee,
            interview_stats_subq.c.interview_count,
            interview_stats_subq.c.last_interviewed_at
        )
        .outerjoin(interview_stats_subq, Employee.id == interview_stats_subq.c.interviewer_id)
        .filter(
            Employee.company_id == job_position.company_id,
            Employee.role.in_([RoleEnum.interviewer, RoleEnum.recruiter]))
    )

    results = query.offset((page - 1) * limit).limit(limit).all()
    total = len(results)

    candidate_out = CandidateMinimal.model_validate(candidate)
    competency_out = CompetencyMinimal.model_validate(competency)
    employee_out = [
        EmployeeInterviewerOut(
            public_id=emp.public_id,
            first_name=emp.first_name,
            last_name=emp.last_name,
            role=emp.role,
            email=emp.email,
            interview_count=count or 0,
            last_interviewed_at=last.isoformat() if last else None,
            job_position=JobMinimal.model_validate(job_position),
            phone_number=PhoneNumberOut.model_validate(emp.phone_number)
        )
        for emp, count, last in results
    ]

    return PaginatedEmployeeResponse(
        total=total,
        page=page,
        limit=limit,
        candidate=candidate_out,
        competency=competency_out,
        employees=employee_out
    )


@router.get("/{job_position_public_id}/applications", response_model=PaginatedApplicationResponse)
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
    # Validate
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
            joinedload(JobApplication.job_position),
            joinedload(JobApplication.interviews)
            .joinedload(JobInterview.competency),
            joinedload(JobApplication.interviews)
            .joinedload(JobInterview.application)
            .joinedload(JobApplication.candidate),
            joinedload(JobApplication.interviews)
            .joinedload(JobInterview.application)
            .joinedload(JobApplication.job_position),
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

    applications = []

    for app in apps:
        interviews = []

        for i in app.interviews:
            interviews.append(
                InterviewOut(
                    public_id=i.public_id,
                    interview_datetime=i.interview_datetime,
                    interview_status=i.interview_status,
                    competency=CompetencyMinimal.model_validate(i.competency),
                    candidate=CandidateMinimal.model_validate(i.application.candidate),
                    job_position=JobMinimal.model_validate(i.application.job_position),
                )
            )

        applications.append({
            "public_id": app.public_id,
            "created_at": app.created_at,
            "status": app.status,
            "candidate": CandidateOut.model_validate(app.candidate),
            "job_position": JobMinimal.model_validate(app.job_position),
            "interviews": interviews,
        })

    return PaginatedApplicationResponse(
        applications=applications,
        job_position=JobMinimal.model_validate(job_position),
        total=total,
        page=page,
        limit=limit,
    )


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


@router.delete("/{job_position_public_id}/{candidate_public_id}", response_model=SuccessResponse)
def delete_candidate_from_job(
        job_position_public_id: str,
        candidate_public_id: str,
        payload: dict = Depends(verify_token),
        db: Session = Depends(get_db)
):
    employee_id = payload["sub"]
    employee = db.query(Employee).filter_by(public_id=employee_id).first()

    if not employee:
        raise HTTPException(status_code=403, detail="Unauthorized")

    candidate = db.query(Candidate).filter_by(public_id=candidate_public_id).first()
    job_position = db.query(JobPosition).filter_by(public_id=job_position_public_id).first()

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
