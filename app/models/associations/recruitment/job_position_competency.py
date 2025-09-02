from sqlalchemy import Table, Column, ForeignKey, Integer
from app.models.base import Base

job_position_competency_mappings = Table(
    "job_position_competency_mappings",
    Base.metadata,
    Column(
        "job_position_id",
        Integer,
        ForeignKey("job_positions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "competency_id",
        Integer,
        ForeignKey("competencies.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
