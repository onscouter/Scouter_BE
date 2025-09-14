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
from app.schemas.new_job import NewJobPayload, Questions, EvaluationCriterion, RubricBlock, Indicator
from app.schemas.success_response import SuccessResponse

router = APIRouter()


@router.post("/new-role", response_model=SuccessResponse)
def new_role(
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

    for block in payload.rubric:
        competency = db.query(Competency).filter_by(name=block.competencyName).first()
        if not competency:
            competency = Competency(
                name=block.competencyName,
                description=block.description
            )
            db.add(competency)
            db.flush()

        job.competencies.append(competency)

        for criterion in block.criteria:
            try:
                score_level = RubricScoreLevel(criterion.score)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid rubric score: {criterion.score}")

            rubric_level = CompetencyRubricLevel(
                competency_id=competency.id,
                level=score_level,
                description=criterion.description
            )
            db.add(rubric_level)
            db.flush()

            for indicator in criterion.indicators:
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

    return SuccessResponse(success=True, message=f"Role created {job.public_id}.")


@router.put("/{role_id}", response_model=SuccessResponse)
def update_role(
        role_id: str,
        payload: NewJobPayload,
        token: dict = Depends(verify_token),
        db: Session = Depends(get_db)
):
    employee_id = token["sub"]

    employee = db.query(Employee).filter_by(public_id=employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Authenticated user not found")

    job = db.query(JobPosition).filter_by(public_id=role_id).first()
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

    for block in payload.rubric:
        competency = db.query(Competency).filter_by(name=block.competencyName).first()
        if not competency:
            competency = Competency(
                name=block.competencyName,
                description=block.description
            )
            db.add(competency)
            db.flush()

        job.competencies.append(competency)

        for criterion in block.criteria:
            try:
                score_level = RubricScoreLevel(criterion.score)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid rubric score: {criterion.score}")

            rubric_level = CompetencyRubricLevel(
                competency_id=competency.id,
                level=score_level,
                description=criterion.description
            )
            db.add(rubric_level)
            db.flush()

            for indicator in criterion.indicators:
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

    return SuccessResponse(success=True, message=f"Role updated: {job.public_id}")


@router.get("/{role_id}", response_model=NewJobPayload)
def get_role(
        role_id: str,
        token: dict = Depends(verify_token),
        db: Session = Depends(get_db),
):
    employee_id = token["sub"]

    employee = db.query(Employee).filter_by(public_id=employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Authenticated user not found")

    job_position = (
        db.query(JobPosition)
        .filter_by(public_id=role_id)
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

    rubric_blocks = []

    for competency in job_position.competencies:
        # Build rubric criteria
        criteria: List[EvaluationCriterion] = []
        for level in competency.rubric_levels:
            indicators = [
                Indicator(competencyId=str(competency.public_id), text=i.indicator_text)
                for i in level.indicators
            ]
            criteria.append(
                EvaluationCriterion(
                    score=level.level.value,
                    description=level.description,
                    indicators=indicators
                )
            )

        # Build interview questions
        questions = [
            Questions(
                id=str(q.public_id),
                text=q.question_text,
                type=q.type
            )
            for q in competency.interview_questions
        ]

        rubric_blocks.append(
            RubricBlock(
                competencyId=str(competency.public_id),
                competencyName=competency.name,
                description=competency.description,
                criteria=criteria,
                questions=questions
            )
        )

    return NewJobPayload(
        title=job_position.title,
        description=job_position.description,
        rubric=rubric_blocks
    )
