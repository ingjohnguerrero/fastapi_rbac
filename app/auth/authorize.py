"""Permission and ownership checks from token claims. No identity-store access."""

from app.auth.principal import Principal

USERS_CREATE = "users:create"
USERS_READ = "users:read"
USERS_UPDATE = "users:update"
USERS_DELETE = "users:delete"
USERS_READ_SELF = "users:read_self"
USERS_UPDATE_SELF = "users:update_self"
USERS_DELETE_SELF = "users:delete_self"
ROLES_READ = "roles:read"
ROLES_GRANT = "roles:grant"
USERS_GRANT = "users:grant"

DEFAULT_PERMISSIONS = (
    USERS_CREATE,
    USERS_READ,
    USERS_UPDATE,
    USERS_DELETE,
    USERS_READ_SELF,
    USERS_UPDATE_SELF,
    USERS_DELETE_SELF,
    ROLES_READ,
    ROLES_GRANT,
    USERS_GRANT,
)

ADMIN_GRANTS = DEFAULT_PERMISSIONS
USER_GRANTS = (USERS_READ_SELF, USERS_UPDATE_SELF, USERS_DELETE_SELF)

ROLE_USER = "user"
ROLE_ADMIN = "admin"
CATALOG_ROLES = frozenset({ROLE_USER, ROLE_ADMIN})


def has_permission(principal: Principal, name: str) -> bool:
    return name in principal.permissions


def can_list_or_create_users(principal: Principal) -> bool:
    return has_permission(principal, USERS_READ)  # list; create checked separately


def can_operate_on_user(
    principal: Principal,
    target_id: int,
    *,
    all_perm: str,
    self_perm: str,
) -> bool:
    """True if the caller may act on target_id. False means HTTP 404 for members."""
    if has_permission(principal, all_perm):
        return True
    return target_id == principal.user_id and has_permission(principal, self_perm)
