from fastapi import HTTPException
from starlette.requests import Request

from app.presentation.routers.dependencies import get_current_user, require_admin


def _request_with_user(user=None) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/users/me",
        "headers": [],
    }
    request = Request(scope)
    if user is not None:
        request.state.current_user = user
    return request


def test_get_current_user_returns_user_from_request_state():
    request = _request_with_user({"id": 1, "role": "ADMIN"})

    user = get_current_user(request, credentials=None)

    assert user["id"] == 1
    assert user["role"] == "ADMIN"


def test_get_current_user_raises_when_not_authenticated():
    request = _request_with_user()

    try:
        get_current_user(request, credentials=None)
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Not authenticated"


def test_require_admin_allows_admin_role():
    request = _request_with_user({"id": 1, "role": "ADMIN"})

    user = require_admin(request)

    assert user["role"] == "ADMIN"


def test_require_admin_denies_non_admin_role():
    request = _request_with_user({"id": 2, "role": "USER"})

    try:
        require_admin(request)
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 403
        assert exc.detail == "Admin access required"
