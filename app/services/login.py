"""Login: one credential read, hybrid permission union, JWT issue."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.auth.hashing import verify_password
from app.auth.tokens import issue_token
from app.models.entities import Role, User
from app.settings import Settings


def load_user_for_login(session: Session, username: str) -> User | None:
    stmt = (
        select(User)
        .options(
            joinedload(User.role).joinedload(Role.permissions),
            joinedload(User.extra_permissions),
        )
        .where(User.username == username)
    )
    return session.scalars(stmt).unique().one_or_none()


def effective_permissions(user: User) -> list[str]:
    names = {p.name for p in user.role.permissions}
    names |= {p.name for p in user.extra_permissions}
    return sorted(names)


def authenticate(
    session: Session,
    username: str,
    password: str,
    settings: Settings,
) -> tuple[str, int] | None:
    user = load_user_for_login(session, username)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    token = issue_token(
        user_id=user.id,
        role=user.role.name,
        permissions=effective_permissions(user),
        settings=settings,
    )
    return token, user.id
