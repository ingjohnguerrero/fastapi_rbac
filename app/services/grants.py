"""Attach permissions to roles or users (hybrid overlay)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Permission, Role, User, roles_permissions, users_permissions


class GrantNotFoundError(Exception):
    pass


class DuplicateGrantError(Exception):
    pass


def _permission(session: Session, name: str) -> Permission:
    row = session.scalar(select(Permission).where(Permission.name == name))
    if row is None:
        row = Permission(name=name)
        session.add(row)
        session.flush()
    return row


def grant_to_role(session: Session, role_id: int, permission_name: str) -> Permission:
    role = session.get(Role, role_id)
    if role is None:
        raise GrantNotFoundError("role")
    perm = _permission(session, permission_name)
    existing = session.execute(
        select(roles_permissions).where(
            roles_permissions.c.role_id == role_id,
            roles_permissions.c.permission_id == perm.id,
        )
    ).first()
    if existing:
        raise DuplicateGrantError
    role.permissions.append(perm)
    session.flush()
    return perm


def grant_to_user(session: Session, user_id: int, permission_name: str) -> Permission:
    user = session.get(User, user_id)
    if user is None:
        raise GrantNotFoundError("user")
    perm = _permission(session, permission_name)
    existing = session.execute(
        select(users_permissions).where(
            users_permissions.c.user_id == user_id,
            users_permissions.c.permission_id == perm.id,
        )
    ).first()
    if existing:
        raise DuplicateGrantError
    user.extra_permissions.append(perm)
    session.flush()
    return perm
