import enum
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class UserRole(str, enum.Enum):
    customer = "Customer"
    admin = "Admin"
    vendor = "Vendor"


def normalize_role_value(raw: str | None) -> str:
    """Map DB/driver quirks (e.g. enum labels) to canonical JWT/UI roles."""
    s = (raw or "").strip()
    if not s:
        return UserRole.customer.value
    for r in UserRole:
        if s.lower() == r.value.lower() or s.lower() == r.name.lower():
            return r.value
    return s


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    # VARCHAR avoids PostgreSQL native ENUM migration issues when roles change.
    role: Mapped[str] = mapped_column(String(32), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
