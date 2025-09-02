from sqlalchemy.orm import Session
from app.models.access_code import AccessCode


def validate_code(code: str, db: Session):
    access = db.query(AccessCode).filter_by(code=code.strip()).first()
    if not access:
        return None, None
    return access.company, access.role
