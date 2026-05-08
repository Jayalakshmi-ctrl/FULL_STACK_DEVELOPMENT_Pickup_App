from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import User, UserRole, normalize_role_value
from .schemas import LoginIn, MeOut, RegisterIn, TokenOut
from .security import create_access_token, hash_password, verify_password
from .settings import settings

app = FastAPI(title="auth-service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ensure_role_column_is_varchar() -> None:
    """If DB was created with a PostgreSQL enum for role, cast to VARCHAR (idempotent)."""
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    ALTER TABLE users
                    ALTER COLUMN role TYPE VARCHAR(32)
                    USING role::text;
                    """
                )
            )
    except Exception:
        # SQLite / column already varchar / table missing — ignore
        pass


@app.on_event("startup")
def _startup():
    Base.metadata.create_all(bind=engine)
    _ensure_role_column_is_varchar()

    # Seed admin + vendor (separate commits so one failure does not block the other)
    for email, password, role_val in (
        (settings.admin_email, settings.admin_password, UserRole.admin.value),
        (settings.vendor_email, settings.vendor_password, UserRole.vendor.value),
    ):
        db = next(get_db())
        try:
            if db.scalar(select(User).where(User.email == email)) is None:
                db.add(User(email=email, password_hash=hash_password(password), role=role_val))
                db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()


@app.post("/auth/register", response_model=MeOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    user = User(
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
        role=UserRole.customer.value,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    return MeOut(email=user.email, role=normalize_role_value(user.role))


@app.post("/auth/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    try:
        ok = verify_password(payload.password, user.password_hash)
    except Exception:
        ok = False
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    role = normalize_role_value(user.role)
    token = create_access_token(sub=str(user.email).strip().lower(), role=role)
    return TokenOut(access_token=token, role=role)


@app.get("/auth/me", response_model=MeOut)
def me(authorization: str | None = None):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return MeOut(email="(use token sub)", role="(use token role)")
