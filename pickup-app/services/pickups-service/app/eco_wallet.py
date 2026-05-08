from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import EcoWallet


def get_or_create_wallet(db: Session, customer_email: str) -> EcoWallet:
    email = customer_email.lower().strip()
    w = db.scalar(select(EcoWallet).where(EcoWallet.customer_email == email))
    if w is None:
        w = EcoWallet(customer_email=email, eco_points_balance=0)
        db.add(w)
        db.flush()
    return w
