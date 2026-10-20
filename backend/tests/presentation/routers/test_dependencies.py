from fastapi import HTTPException
from starlette.requests import Request

from app.main import app
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

    user = require_admin(get_current_user(request, credentials=None))

    assert user["role"] == "ADMIN"


def test_require_admin_denies_non_admin_role():
    request = _request_with_user({"id": 2, "role": "USER"})

    try:
        require_admin(get_current_user(request, credentials=None))
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 403
        assert exc.detail == "Admin access required"


def test_openapi_declares_bearer_for_protected_endpoints():
    schema = app.openapi()
    public_operations = {
        ("/auth/login", "post"),
        ("/auth/reset-password", "post"),
        ("/health", "get"),
        ("/", "get"),
    }

    assert schema["components"]["securitySchemes"]["HTTPBearer"] == {
        "type": "http",
        "scheme": "bearer",
    }

    for path, path_item in schema["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            if (path, method) in public_operations:
                continue

            assert {"HTTPBearer": []} in operation.get("security", []), (
                f"{method.upper()} {path} must declare HTTPBearer security"
            )
