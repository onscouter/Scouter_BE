from fastapi import Depends, HTTPException, status
from typing import Callable, List
from app.core.auth import verify_token


def require_roles(allowed_roles: List[str]) -> Callable:
    def guard(payload: dict = Depends(verify_token)) -> dict:
        roles = payload.get("roles")

        if not isinstance(roles, list):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing 'roles' in token",
            )

        if not any(role in roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )

        return payload  # Pass payload downstream if needed

    return guard


