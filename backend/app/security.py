from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

ALLOWED_REPORT_ROLES = {"admin", "manager", "analyst"}


def require_report_viewer_role(x_role: str | None = Header(default=None)) -> str:
    if x_role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing role header",
        )
    role = x_role.lower()
    if role not in ALLOWED_REPORT_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view reports",
        )
    return role


def role_dependency(role: str = Depends(require_report_viewer_role)) -> str:
    return role
