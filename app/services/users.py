"""User CRUD after authorization has already allowed the call."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.auth.authorize import CATALOG_ROLES
from app.auth.hashing import hash_password
from app.models.entities import Role, User


class UserConflictError(Exception):
    pass


class InvalidRoleError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


def _role_by_name(session: Session, name: str) -> Role:
    if name not in CATALOG_ROLES:
        raise InvalidRoleError(name)
    role = session.scalar(select(Role).where(Role.name == name))
    if role is None:
        raise InvalidRoleError(name)
    return role


def public_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.name,
    }


def get_user(session: Session, user_id: int) -> User | None:
    stmt = select(User).options(joinedload(User.role)).where(User.id == user_id)
    return session.scalars(stmt).unique().one_or_none()


def list_users(session: Session) -> list[User]:
    stmt = select(User).options(joinedload(User.role)).order_by(User.id)
    return list(session.scalars(stmt).unique().all())


def create_user(
    session: Session,
    *,
    username: str,
    email: str,
    password: str,
    role: str,
) -> User:
    role_row = _role_by_name(session, role)
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role_id=role_row.id,
    )
    session.add(user)
    try:
        session.flush()
    except IntegrityError as exc:
        raise UserConflictError from exc
    user.role = role_row
    return user


def update_user(
    session: Session,
    user: User,
    *,
    username: str | None = None,
    email: str | None = None,
    password: str | None = None,
    role: str | None = None,
) -> User:
    if username is not None:
        user.username = username
    if email is not None:
        user.email = email
    if password is not None:
        user.hashed_password = hash_password(password)
    if role is not None:
        user.role_id = _role_by_name(session, role).id
    try:
        session.flush()
    except IntegrityError as exc:
        raise UserConflictError from exc
    if role is not None:
        user.role = _role_by_name(session, role)
    return user


def delete_user(session: Session, user: User) -> None:
    session.delete(user)
    session.flush()
