import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.settings import settings

_security = HTTPBasic(auto_error=False)


def require_auth(credentials: HTTPBasicCredentials | None = Depends(_security)) -> None:
    """No-op unless BASIC_AUTH_USER/BASIC_AUTH_PASS are set in the environment.

    This is a convenience layer for a LAN-only appliance, not real security -
    it's cleartext without TLS in front of it.
    """
    if not settings.basic_auth_user or not settings.basic_auth_pass:
        return

    valid = credentials is not None and (
        secrets.compare_digest(credentials.username, settings.basic_auth_user)
        and secrets.compare_digest(credentials.password, settings.basic_auth_pass)
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
