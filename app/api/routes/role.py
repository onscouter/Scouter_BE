from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.init_db import get_db
from app.core.auth import verify_token
from app.models import (
    Employee,
    Company,
    JobPosition,
    Competency,
    CompetencyRubricLevel,
    EvaluationIndicator,
    InterviewQuestion,
    JobType,
    RubricScoreLevel,
    TypeLabel,
)
from app.schemas.new_job import NewJobPayload
from app.schemas.success_response import SuccessResponse

router = APIRouter()


@router.post("/new-role")
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

