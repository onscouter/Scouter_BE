import os

from slowapi import Limiter
from app.core.auth import get_user_id

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

limiter = Limiter(
    key_func=get_user_id,
    storage_uri=REDIS_URL,
    enabled=True
)