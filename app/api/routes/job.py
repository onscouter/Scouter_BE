from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.db.init_db import get_db
from app.core.auth import verify_token
from app.models import (
    Employee,
    Company,
    JobPosition,
    Competency,
    CompetencyRubricLevel,
    EvaluationIndicator,
    JobType,
    InterviewQuestion,
    RubricScoreLevel,
    TypeLabel,
)
from app.schemas.competency import CompetencyOut
from app.schemas.new_job import NewJobPayload
from app.schemas.rubric import Questions, Indicator, RubricLevel
from app.schemas.success_response import SuccessResponse

router = APIRouter()


@router.post("/new-job", response_model=SuccessResponse)
def new_job(
        payload: NewJobPayload,
        token: dict = Depends(verify_token),
        db: Session = Depends(get_db)
):
    employee_id = token["sub"]

    employee = db.query(Employee).filter_by(public_id=employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Authenticated user not found")

    company = db.query(Company).filter_by(id=employee.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="User's company not found")

    job = JobPosition(
        title=payload.title,
        description=payload.description,
        company_id=company.id,
        job_type=JobType.EXTERNAL
    )
    db.add(job)
    db.flush()

    for block in payload.competencies:
        competency = db.query(Competency).filter_by(name=block.name).first()
        if not competency:
            competency = Competency(
                name=block.name,
                description=block.description
            )
            db.add(competency)
            db.flush()

        job.competencies.append(competency)

        for rubric_level in block.rubric_levels:
            try:
                score_level = RubricScoreLevel(rubric_level.level)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid rubric score: {criterion.score}")

            rubric_level = CompetencyRubricLevel(
                competency_id=competency.id,
                level=score_level,
                description=rubric_level.description,
                job_position_id=job.id
            )
            db.add(rubric_level)
            db.flush()

            for indicator in rubric_level.indicators:
                db.add(EvaluationIndicator(
                    rubric_level_id=rubric_level.id,
                    indicator_text=indicator.text
                ))

        for q in block.questions:
            try:
                question_type = TypeLabel[q.type.upper()]
            except (KeyError, AttributeError):
                raise HTTPException(status_code=400, detail=f"Invalid question type: {q.type}")

            db.add(InterviewQuestion(
                question_text=q.text,
                type=question_type,
                competency_id=competency.id,
                job_position_id=job.id
            ))

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return SuccessResponse(success=True, message=f"Job created {job.public_id}.")


@router.put("/{job_position_public_id}", response_model=SuccessResponse)
def update_job(
        job_position_public_id: str,
        payload: NewJobPayload,
        token: dict = Depends(verify_token),
        db: Session = Depends(get_db)
):
    employee_id = token["sub"]

    employee = db.query(Employee).filter_by(public_id=employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Authenticated user not found")

    job = db.query(JobPosition).filter_by(public_id=job_position_public_id).first()
    if not job or job.company_id != employee.company_id:
        raise HTTPException(status_code=404, detail="Job not found or unauthorized")

    job.title = payload.title
    job.description = payload.description

    for competency in job.competencies:
        rubric_levels = db.query(CompetencyRubricLevel).filter_by(competency_id=competency.id).all()
        for level in rubric_levels:
            db.query(EvaluationIndicator).filter_by(rubric_level_id=level.id).delete()

        db.query(CompetencyRubricLevel).filter_by(competency_id=competency.id).delete()
        db.query(InterviewQuestion).filter_by(competency_id=competency.id).delete()

    job.competencies.clear()

    for block in payload.competencies:
        competency = db.query(Competency).filter_by(name=block.name).first()
        if not competency:
            competency = Competency(
                name=block.name,
                description=block.description
            )
            db.add(competency)
            db.flush()

        job.competencies.append(competency)

        for rubric_level in block.rubric_levels:
            try:
                score_level = RubricScoreLevel(rubric_level.level)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid rubric score: {criterion.score}")

            rubric_level = CompetencyRubricLevel(
                competency_id=competency.id,
                level=score_level,
                description=rubric_level.description
            )
            db.add(rubric_level)
            db.flush()

            for indicator in rubric_level.indicators:
                db.add(EvaluationIndicator(
                    rubric_level_id=rubric_level.id,
                    indicator_text=indicator.text
                ))

        for q in block.questions:
            try:
                question_type = TypeLabel[q.type.upper()]
            except (KeyError, AttributeError):
                raise HTTPException(status_code=400, detail=f"Invalid question type: {q.type}")

            db.add(InterviewQuestion(
                question_text=q.text,
                type=question_type,
                competency_id=competency.id
            ))

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return SuccessResponse(success=True, message=f"Job updated: {job.public_id}")


@router.get("/{job_position_public_id}", response_model=NewJobPayload)
def get_job(
        job_position_public_id: str,
        token: dict = Depends(verify_token),
        db: Session = Depends(get_db),
):
    employee_id = token["sub"]

    employee = db.query(Employee).filter_by(public_id=employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Authenticated user not found")

    job_position = (
        db.query(JobPosition)
        .filter_by(public_id=job_position_public_id)
        .options(
            joinedload(JobPosition.competencies)
            .joinedload(Competency.rubric_levels)
            .joinedload(CompetencyRubricLevel.indicators),
            joinedload(JobPosition.competencies)
            .joinedload(Competency.interview_questions)
        )
        .first()
    )

    if not job_position:
        raise HTTPException(status_code=404, detail="Job position not found")

    if job_position.company_id != employee.company_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to company data")

    competencies: List[CompetencyOut] = []

    for competency in job_position.competencies:
        # Build rubric criteria
        rubric_levels: List[RubricLevel] = []
        for level in competency.rubric_levels:
            indicators = [
                Indicator(
                    public_id=i.public_id,
                    indicator_text=i.indicator_text
                )
                for i in level.indicators
            ]
            rubric_levels.append(
                RubricLevel(
                    public_id=level.public_id,
                    level=level.level.value,
                    description=level.description,
                    indicators=indicators
                )
            )

        questions = [Questions.model_validate(q) for q in competency.interview_questions]

        competencies.append(
            CompetencyOut(
                public_id=competency.public_id,
                name=competency.name,
                description=competency.description,
                rubric_levels=rubric_levels,
                questions=questions
            )
        )

    return NewJobPayload(
        title=job_position.title,
        description=job_position.description,
        competencies=competencies
    )
