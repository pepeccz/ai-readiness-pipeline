"""
app/api/admin/users_routes — read-only user listing for admin UIs.

Currently exposes:
  GET /api/admin/users — list active admin users for consultant assignment dropdowns.

Auth: admin session (Depends(require_admin)).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import require_admin
from app.db.session import get_db
from app.models.user import User

router = APIRouter(tags=["admin", "users"])


class UserOption(BaseModel):
    id: str
    email: str
    display_name: str


@router.get("/users", response_model=list[UserOption])
async def list_users(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[UserOption]:
    """Return active users — used for consultor assignment dropdowns."""
    result = await db.execute(
        select(User)
        .where(User.is_active.is_(True))
        .order_by(User.email)
    )
    return [
        UserOption(
            id=str(u.id),
            email=u.email,
            display_name=u.display_name or u.email,
        )
        for u in result.scalars().all()
    ]
