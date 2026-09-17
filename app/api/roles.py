"""Role listing and role permission grants."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.api.deps import require_permission
from app.api.errors import conflict, not_found
from app.auth.authorize import ROLES_GRANT, ROLES_READ
from app.auth.principal import Principal
from app.models.entities import Role
from app.services.grants import DuplicateGrantError, GrantNotFoundError, grant_to_role

router = APIRouter(tags=["roles"])


class RolePublic(BaseModel):
    id: int
    name: str


class GrantBody(BaseModel):
    name: str = Field(min_length=1)


@router.get("/roles", response_model=list[RolePublic])
def read_roles(
    principal: Principal = Depends(require_permission(ROLES_READ)),
    db: Session = Depends(get_db),
) -> list[dict]:
    rows = db.scalars(select(Role).order_by(Role.id)).all()
    return [{"id": r.id, "name": r.name} for r in rows]


@router.post("/roles/{role_id}/permissions", status_code=201)
def post_role_permission(
    role_id: int,
    body: GrantBody,
    principal: Principal = Depends(require_permission(ROLES_GRANT)),
    db: Session = Depends(get_db),
) -> dict:
    try:
        perm = grant_to_role(db, role_id, body.name)
    except GrantNotFoundError:
        not_found()
    except DuplicateGrantError:
        conflict()
    return {"id": perm.id, "name": perm.name}
