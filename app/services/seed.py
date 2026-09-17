"""Seed roles, default permission catalog, and first administrator."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.authorize import (
    ADMIN_GRANTS,
    DEFAULT_PERMISSIONS,
    ROLE_ADMIN,
    ROLE_USER,
    USER_GRANTS,
)
from app.auth.hashing import hash_password
from app.models.entities import Permission, Role, User


def _ensure_grants(role: Role, names: tuple[str, ...], by_perm: dict[str, Permission]) -> None:
    existing = {p.name for p in role.permissions}
    for name in names:
        if name not in existing:
            role.permissions.append(by_perm[name])


def seed_catalog(session: Session) -> None:
    for name in (ROLE_USER, ROLE_ADMIN):
        if session.scalar(select(Role).where(Role.name == name)) is None:
            session.add(Role(name=name))
    session.flush()

    for name in DEFAULT_PERMISSIONS:
        if session.scalar(select(Permission).where(Permission.name == name)) is None:
            session.add(Permission(name=name))
    session.flush()

    by_perm = {p.name: p for p in session.scalars(select(Permission)).all()}
    admin = session.scalar(select(Role).where(Role.name == ROLE_ADMIN))
    user = session.scalar(select(Role).where(Role.name == ROLE_USER))
    assert admin is not None and user is not None

    _ensure_grants(admin, ADMIN_GRANTS, by_perm)
    _ensure_grants(user, USER_GRANTS, by_perm)
    session.flush()


def admin_exists(session: Session) -> bool:
    admin_role = session.scalar(select(Role).where(Role.name == ROLE_ADMIN))
    if admin_role is None:
        return False
    return session.scalar(select(User).where(User.role_id == admin_role.id).limit(1)) is not None


def create_first_admin(
    session: Session,
    *,
    username: str,
    email: str,
    password: str,
) -> User:
    admin_role = session.scalar(select(Role).where(Role.name == ROLE_ADMIN))
    if admin_role is None:
        raise RuntimeError("admin role missing; seed_catalog first")
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role_id=admin_role.id,
    )
    session.add(user)
    session.flush()
    return user
