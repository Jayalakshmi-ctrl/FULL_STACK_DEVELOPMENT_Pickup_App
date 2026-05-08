from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .settings import settings

bearer = HTTPBearer(auto_error=False)


def require_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        payload = jwt.decode(
            creds.credentials,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    sub = payload.get("sub")
    role = payload.get("role")
    if not sub or not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")
    # Match auth-service: lowercase email; trim role (avoids 403/empty lists from casing drift).
    return {"email": str(sub).strip().lower(), "role": str(role).strip()}


def require_admin(user: dict = Depends(require_user)) -> dict:
    if user["role"].lower() != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


def require_customer(user: dict = Depends(require_user)) -> dict:
    if user["role"].lower() != "customer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer only")
    return user


def require_vendor(user: dict = Depends(require_user)) -> dict:
    if user["role"].lower() != "vendor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor only")
    return user
