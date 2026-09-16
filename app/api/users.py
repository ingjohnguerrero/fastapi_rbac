"""User HTTP routes. Authorize from token; load rows only after allow."""

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.api.deps import get_principal, require_permission
from app.api.errors import conflict, not_found
from app.auth.authorize import (
    USERS_CREATE,
    USERS_DELETE,
    USERS_DELETE_SELF,
    USERS_GRANT,
    USERS_READ,
    USERS_READ_SELF,
    USERS_UPDATE,
    USERS_UPDATE_SELF,
    can_operate_on_user,
    has_permission,
)
from app.auth.principal import Principal
from app.services.grants import DuplicateGrantError, GrantNotFoundError, grant_to_user
from app.services.users import (
    InvalidRoleError,
    UserConflictError,
    create_user,
    delete_user,
    get_user,
    list_users,
    public_user,
    update_user,
)

router = APIRouter(tags=["users"])


class UserPublic(BaseModel):
    id: int
    username: str
    email: str
    role: str


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1)
    role: str


class UserPatchMember(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str | None = Field(default=None, min_length=1, max_length=128)
    email: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=1)


class UserPatchAdmin(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=128)
    email: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=1)
    role: str | None = None


class GrantBody(BaseModel):
    name: str = Field(min_length=1)


def _guard_user_access(principal: Principal, user_id: int, *, all_perm: str, self_perm: str) -> None:
    if not can_operate_on_user(principal, user_id, all_perm=all_perm, self_perm=self_perm):
        not_found()


@router.get("/users/me", response_model=UserPublic)
def read_me(
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
) -> dict:
    _guard_user_access(principal, principal.user_id, all_perm=USERS_READ, self_perm=USERS_READ_SELF)
    user = get_user(db, principal.user_id)
    if user is None:
        not_found()
    return public_user(user)


@router.get("/users", response_model=list[UserPublic])
def read_users(
    principal: Principal = Depends(require_permission(USERS_READ)),
    db: Session = Depends(get_db),
) -> list[dict]:
    return [public_user(u) for u in list_users(db)]


@router.post("/users", response_model=UserPublic, status_code=201)
def post_user(
    body: UserCreate,
    principal: Principal = Depends(require_permission(USERS_CREATE)),
    db: Session = Depends(get_db),
) -> dict:
    try:
        user = create_user(
            db,
            username=body.username,
            email=body.email,
            password=body.password,
            role=body.role,
        )
    except InvalidRoleError:
        raise HTTPException(status_code=422, detail="Invalid role") from None
    except UserConflictError:
        conflict()
    return public_user(user)


@router.get("/users/{user_id}", response_model=UserPublic)
def read_user(
    user_id: int,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
) -> dict:
    _guard_user_access(principal, user_id, all_perm=USERS_READ, self_perm=USERS_READ_SELF)
    user = get_user(db, user_id)
    if user is None:
        not_found()
    return public_user(user)


@router.patch("/users/{user_id}", response_model=UserPublic)
def patch_user(
    user_id: int,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    payload: dict = Body(default_factory=dict),
) -> dict:
    _guard_user_access(principal, user_id, all_perm=USERS_UPDATE, self_perm=USERS_UPDATE_SELF)
    user = get_user(db, user_id)
    if user is None:
        not_found()
    try:
        if has_permission(principal, USERS_UPDATE):
            parsed = UserPatchAdmin.model_validate(payload)
            user = update_user(
                db,
                user,
                username=parsed.username,
                email=parsed.email,
                password=parsed.password,
                role=parsed.role,
            )
        else:
            parsed_m = UserPatchMember.model_validate(payload)
            user = update_user(
                db,
                user,
                username=parsed_m.username,
                email=parsed_m.email,
                password=parsed_m.password,
                role=None,
            )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from None
    except InvalidRoleError:
        raise HTTPException(status_code=422, detail="Invalid role") from None
    except UserConflictError:
        conflict()
    return public_user(user)


@router.delete("/users/{user_id}", status_code=204)
def remove_user(
    user_id: int,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
) -> None:
    _guard_user_access(principal, user_id, all_perm=USERS_DELETE, self_perm=USERS_DELETE_SELF)
    user = get_user(db, user_id)
    if user is None:
        not_found()
    delete_user(db, user)


@router.post("/users/{user_id}/permissions", status_code=201)
def post_user_permission(
    user_id: int,
    body: GrantBody,
    principal: Principal = Depends(require_permission(USERS_GRANT)),
    db: Session = Depends(get_db),
) -> dict:
    try:
        perm = grant_to_user(db, user_id, body.name)
    except GrantNotFoundError:
        not_found()
    except DuplicateGrantError:
        conflict()
    return {"id": perm.id, "name": perm.name}
