"""AC-FR-11: authorize decision uses claims only (no identity-store session)."""

import inspect

from app.api import deps
from app.auth import authorize, principal, tokens
from app.auth.authorize import USERS_READ, USERS_READ_SELF, can_operate_on_user, has_permission
from app.auth.principal import Principal


def test_ac_fr_11_authorize_modules_do_not_open_a_session():
    for module in (authorize, principal, tokens, deps):
        source = inspect.getsource(module)
        assert "adapters.db" not in source
        assert "Session" not in source
        assert "get_db" not in source


def test_ac_fr_11_decision_from_claims_only():
    admin = Principal(user_id=1, role="admin", permissions=frozenset({USERS_READ}))
    member = Principal(user_id=2, role="user", permissions=frozenset({USERS_READ_SELF}))
    assert has_permission(admin, USERS_READ)
    assert not has_permission(member, USERS_READ)
    assert can_operate_on_user(member, 2, all_perm=USERS_READ, self_perm=USERS_READ_SELF)
    assert not can_operate_on_user(member, 99, all_perm=USERS_READ, self_perm=USERS_READ_SELF)
