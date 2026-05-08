import logging
from datetime import date
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from .authz import require_admin, require_customer, require_user, require_vendor
from .db import Base, engine, get_db
from .eco_wallet import get_or_create_wallet
from .models import (
    Pickup,
    PickupStatus,
    PhysicalReward,
    PlasticVerification,
    Redemption,
    RedemptionStatus,
    RewardType,
)
from .schemas import (
    AdminRedemptionOut,
    PhysicalRewardOut,
    PickupCreateIn,
    PickupOut,
    PickupStatusUpdateIn,
    PlasticVerificationOut,
    RedeemIn,
    RedeemOut,
    RedemptionHistoryItem,
    RewardHistoryItem,
    RewardsOut,
    ScheduleDeliveryIn,
    VerifyPlasticIn,
    VerifyPlasticOut,
    WalletOut,
)
from .settings import settings

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="pickups-service", version="1.0.0")


def _as_plain_str(v) -> str:
    """ORM may return Enum members or plain strings depending on DB column type."""
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    return getattr(v, "value", str(v))

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ensure_pickup_status_varchar() -> None:
    """Migrate legacy PostgreSQL enum column to VARCHAR if present (best-effort per step)."""
    steps = [
        "ALTER TABLE pickups ALTER COLUMN status DROP DEFAULT",
        """
        ALTER TABLE pickups
        ALTER COLUMN status TYPE VARCHAR(32)
        USING status::text;
        """,
        "ALTER TABLE pickups ALTER COLUMN status SET DEFAULT 'Requested'",
    ]
    for raw in steps:
        stmt = text(raw.strip())
        try:
            with engine.begin() as conn:
                conn.execute(stmt)
        except Exception as e:
            logger.warning("pickups.status migration step skipped: %s | %s", raw.strip()[:60], e)


def _ensure_redemptions_delivery_date() -> None:
    """Add redemptions.delivery_date on older DBs (best-effort)."""
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE redemptions ADD COLUMN IF NOT EXISTS delivery_date DATE"))
    except Exception as e:
        logger.warning("redemptions.delivery_date migration skipped or failed: %s", e)


def _ensure_redemptions_sent_at() -> None:
    """Add redemptions.sent_at on older DBs (best-effort)."""
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE redemptions ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ"))
    except Exception as e:
        logger.warning("redemptions.sent_at migration skipped or failed: %s", e)


def _seed_catalog(db: Session) -> None:
    items = [
        PhysicalReward(
            slug="native-sapling",
            name="Native tree sapling",
            reward_type=RewardType.sapling,
            description="One sapling for your home garden.",
            points_cost=500,
            active=True,
        ),
        PhysicalReward(
            slug="organic-seeds-mix",
            name="Organic seed starter pack",
            reward_type=RewardType.organic_seeds,
            description="Mixed organic vegetable and herb seeds.",
            points_cost=220,
            active=True,
        ),
        PhysicalReward(
            slug="compost-bag",
            name="Home compost bag (5 kg)",
            reward_type=RewardType.compost,
            description="Nutrient-rich compost for pots and beds.",
            points_cost=350,
            active=True,
        ),
        # Medicinal plant saplings (6 varieties)
        PhysicalReward(
            slug="medicinal-tulsi",
            name="Tulsi (Holy Basil) sapling",
            reward_type=RewardType.sapling,
            description="Fragrant tulsi sapling for your balcony or garden.",
            points_cost=320,
            active=True,
        ),
        PhysicalReward(
            slug="medicinal-aloe-vera",
            name="Aloe vera plant",
            reward_type=RewardType.sapling,
            description="Hardy aloe plant — low water, easy care.",
            points_cost=380,
            active=True,
        ),
        PhysicalReward(
            slug="medicinal-neem",
            name="Neem sapling",
            reward_type=RewardType.sapling,
            description="Neem sapling — a classic medicinal and shade tree.",
            points_cost=520,
            active=True,
        ),
        PhysicalReward(
            slug="medicinal-mint",
            name="Mint plant",
            reward_type=RewardType.sapling,
            description="Fresh mint plant for teas and home remedies.",
            points_cost=260,
            active=True,
        ),
        PhysicalReward(
            slug="medicinal-lemongrass",
            name="Lemongrass plant",
            reward_type=RewardType.sapling,
            description="Aromatic lemongrass — great for tea and cooking.",
            points_cost=300,
            active=True,
        ),
        PhysicalReward(
            slug="medicinal-ashwagandha",
            name="Ashwagandha sapling",
            reward_type=RewardType.sapling,
            description="Ashwagandha (Withania somnifera) starter plant.",
            points_cost=600,
            active=True,
        ),
    ]

    existing = set(db.scalars(select(PhysicalReward.slug)).all())
    added = 0
    for it in items:
        if it.slug in existing:
            continue
        db.add(it)
        added += 1
    if added:
        db.commit()


@app.on_event("startup")
def _startup():
    Base.metadata.create_all(bind=engine)
    _ensure_pickup_status_varchar()
    _ensure_redemptions_delivery_date()
    _ensure_redemptions_sent_at()
    db = next(get_db())
    try:
        _seed_catalog(db)
    finally:
        db.close()


def _to_out(p: Pickup) -> PickupOut:
    st = _as_plain_str(p.status)
    return PickupOut(
        id=p.id,
        customer_email=p.customer_email,
        address=p.address,
        pickup_date=p.pickup_date,
        status=st,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@app.get("/pickups", response_model=list[PickupOut])
def list_pickups(user: dict = Depends(require_user), db: Session = Depends(get_db)):
    if user["role"].lower() == "vendor":
        return []
    if user["role"].lower() == "admin":
        pickups = db.scalars(select(Pickup).order_by(Pickup.id.desc())).all()
    else:
        pickups = db.scalars(
            select(Pickup)
            .where(Pickup.customer_email == user["email"])
            .order_by(Pickup.id.desc())
        ).all()
    return [_to_out(p) for p in pickups]


@app.post("/pickups", response_model=PickupOut, status_code=201)
def create_pickup(payload: PickupCreateIn, user: dict = Depends(require_customer), db: Session = Depends(get_db)):
    if payload.pickup_date < date.today():
        raise HTTPException(status_code=400, detail="pickup_date cannot be in the past")

    cust = str(user["email"]).lower().strip()

    def _insert() -> Pickup:
        p = Pickup(
            customer_email=cust,
            address=payload.address,
            pickup_date=payload.pickup_date,
            status=PickupStatus.requested.value,
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        return p

    try:
        pickup = _insert()
    except SQLAlchemyError as e:
        db.rollback()
        msg = str(e).lower()
        # Old DBs often still have a native ENUM for status; first INSERT fails until we migrate.
        if "enum" in msg or "invalid input" in msg or "wrong data type" in msg:
            logger.warning("pickups insert failed (likely status enum); retrying after migration: %s", e)
            _ensure_pickup_status_varchar()
            try:
                pickup = _insert()
            except SQLAlchemyError as e2:
                db.rollback()
                logger.exception("create_pickup failed after migration")
                raise HTTPException(
                    status_code=500,
                    detail="Could not save pickup. Try: docker compose down -v && docker compose up --build",
                ) from e2
        else:
            logger.exception("create_pickup failed")
            raise HTTPException(
                status_code=500,
                detail="Could not save pickup. Check pickups-service logs.",
            ) from e

    return _to_out(pickup)


@app.patch("/pickups/{pickup_id}/status", response_model=PickupOut)
def update_status(
    pickup_id: int,
    payload: PickupStatusUpdateIn,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if payload.status not in (PickupStatus.picked_up.value, PickupStatus.requested.value):
        raise HTTPException(status_code=400, detail="Invalid status")
    pickup = db.get(Pickup, pickup_id)
    if pickup is None:
        raise HTTPException(status_code=404, detail="Pickup not found")

    prev_status = _as_plain_str(pickup.status)
    pickup.status = payload.status

    # If admin marks as picked up and provides weight, credit Eco-Points immediately.
    # Guard against double-credit by only crediting on the transition to Picked Up.
    should_credit = (
        prev_status != PickupStatus.picked_up.value
        and payload.status == PickupStatus.picked_up.value
        and payload.weight_kg is not None
    )
    if should_credit:
        cust = str(pickup.customer_email).lower().strip()
        awarded = max(1, int(round(payload.weight_kg * settings.eco_points_per_kg)))
        row = PlasticVerification(
            vendor_email=str(user["email"]).lower().strip(),
            customer_email=cust,
            weight_kg=float(payload.weight_kg),
            eco_points_awarded=awarded,
            notes=payload.notes,
        )
        db.add(row)
        wallet = get_or_create_wallet(db, cust)
        wallet.eco_points_balance += awarded

    db.add(pickup)
    db.commit()
    db.refresh(pickup)
    return _to_out(pickup)


@app.post("/eco/verify-plastic", response_model=VerifyPlasticOut, status_code=201)
def verify_plastic(payload: VerifyPlasticIn, user: dict = Depends(require_vendor), db: Session = Depends(get_db)):
    cust = str(payload.customer_email).lower().strip()
    awarded = max(1, int(round(payload.weight_kg * settings.eco_points_per_kg)))
    row = PlasticVerification(
        vendor_email=user["email"].lower().strip(),
        customer_email=cust,
        weight_kg=payload.weight_kg,
        eco_points_awarded=awarded,
        notes=payload.notes,
    )
    db.add(row)
    wallet = get_or_create_wallet(db, cust)
    wallet.eco_points_balance += awarded
    db.commit()
    db.refresh(row)
    db.refresh(wallet)
    return VerifyPlasticOut(
        id=row.id,
        customer_email=row.customer_email,
        weight_kg=row.weight_kg,
        eco_points_awarded=row.eco_points_awarded,
        vendor_email=row.vendor_email,
        new_balance=wallet.eco_points_balance,
        created_at=row.created_at,
    )


@app.get("/eco/wallet/me", response_model=WalletOut)
def wallet_me(user: dict = Depends(require_customer), db: Session = Depends(get_db)):
    w = get_or_create_wallet(db, user["email"])
    db.commit()
    return WalletOut(customer_email=w.customer_email, eco_points_balance=w.eco_points_balance)


@app.get("/catalog/rewards", response_model=list[PhysicalRewardOut])
def list_catalog(_: dict = Depends(require_user), db: Session = Depends(get_db)):
    rewards = db.scalars(select(PhysicalReward).where(PhysicalReward.active.is_(True)).order_by(PhysicalReward.id)).all()
    return [
        PhysicalRewardOut(
            id=r.id,
            slug=r.slug,
            name=r.name,
            reward_type=_as_plain_str(r.reward_type),
            description=r.description,
            points_cost=r.points_cost,
        )
        for r in rewards
    ]


@app.post("/catalog/redeem", response_model=RedeemOut, status_code=201)
def redeem(payload: RedeemIn, user: dict = Depends(require_customer), db: Session = Depends(get_db)):
    reward = db.get(PhysicalReward, payload.reward_id)
    if reward is None or not reward.active:
        raise HTTPException(status_code=404, detail="Reward not found")
    wallet = get_or_create_wallet(db, user["email"])
    if wallet.eco_points_balance < reward.points_cost:
        raise HTTPException(status_code=400, detail="Not enough Eco-Points")
    wallet.eco_points_balance -= reward.points_cost
    red = Redemption(
        customer_email=user["email"].lower().strip(),
        reward_id=reward.id,
        points_spent=reward.points_cost,
        status=RedemptionStatus.requested,
    )
    db.add(red)
    db.commit()
    db.refresh(red)
    return RedeemOut(
        id=red.id,
        reward_name=reward.name,
        points_spent=red.points_spent,
        remaining_balance=wallet.eco_points_balance,
        status=_as_plain_str(red.status),
        delivery_date=red.delivery_date,
        sent_at=red.sent_at,
        created_at=red.created_at,
    )


@app.get("/admin/redemptions", response_model=list[AdminRedemptionOut])
def admin_list_redemptions(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Redemption)
        .options(joinedload(Redemption.reward))
        .order_by(Redemption.id.desc())
    ).unique().all()
    return [
        AdminRedemptionOut(
            id=r.id,
            customer_email=r.customer_email,
            reward_name=r.reward.name if r.reward else "",
            reward_type=_as_plain_str(r.reward.reward_type) if r.reward else "",
            points_spent=r.points_spent,
            status=_as_plain_str(r.status),
            delivery_date=r.delivery_date,
            sent_at=r.sent_at,
            created_at=r.created_at,
        )
        for r in rows
    ]


@app.patch("/admin/redemptions/{redemption_id}/schedule", response_model=AdminRedemptionOut)
def admin_schedule_delivery(
    redemption_id: int,
    payload: ScheduleDeliveryIn,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if payload.delivery_date < date.today():
        raise HTTPException(status_code=400, detail="delivery_date cannot be in the past")
    red = db.get(Redemption, redemption_id)
    if red is None:
        raise HTTPException(status_code=404, detail="Redemption not found")
    red.delivery_date = payload.delivery_date
    red.status = RedemptionStatus.fulfilled
    # record when it was sent/fulfilled so the customer's "When" can reflect delivery action
    red.sent_at = datetime.utcnow()
    db.add(red)
    db.commit()
    db.refresh(red)
    reward = db.get(PhysicalReward, red.reward_id)
    return AdminRedemptionOut(
        id=red.id,
        customer_email=red.customer_email,
        reward_name=reward.name if reward else "",
        reward_type=_as_plain_str(reward.reward_type) if reward else "",
        points_spent=red.points_spent,
        status=_as_plain_str(red.status),
        delivery_date=red.delivery_date,
        sent_at=red.sent_at,
        created_at=red.created_at,
    )


@app.get("/rewards/me", response_model=RewardsOut)
def rewards_me(user: dict = Depends(require_customer), db: Session = Depends(get_db)):
    wallet = get_or_create_wallet(db, user["email"])
    db.commit()

    ver_rows = db.scalars(
        select(PlasticVerification)
        .where(PlasticVerification.customer_email == user["email"].lower().strip())
        .order_by(PlasticVerification.id.desc())
    ).all()
    plastic_history = [
        PlasticVerificationOut(
            id=v.id,
            weight_kg=v.weight_kg,
            eco_points_awarded=v.eco_points_awarded,
            vendor_email=v.vendor_email,
            created_at=v.created_at,
            notes=v.notes,
        )
        for v in ver_rows
    ]

    red_rows = db.scalars(
        select(Redemption)
        .options(joinedload(Redemption.reward))
        .where(Redemption.customer_email == user["email"].lower().strip())
        .order_by(Redemption.id.desc())
    ).unique().all()
    redemptions = [
        RedemptionHistoryItem(
            id=r.id,
            reward_name=r.reward.name if r.reward else "",
            reward_type=_as_plain_str(r.reward.reward_type) if r.reward else "",
            points_spent=r.points_spent,
            status=_as_plain_str(r.status),
            delivery_date=r.delivery_date,
            sent_at=r.sent_at,
            created_at=r.created_at,
        )
        for r in red_rows
    ]

    pickups = db.scalars(
        select(Pickup).where(Pickup.customer_email == user["email"].lower().strip()).order_by(Pickup.id.desc())
    ).all()
    pickup_history = [
        RewardHistoryItem(
            pickup_id=p.id,
            pickup_date=p.pickup_date,
            status=_as_plain_str(p.status),
            points_earned=0,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in pickups
    ]

    return RewardsOut(
        eco_points_balance=wallet.eco_points_balance,
        eco_points_per_kg=settings.eco_points_per_kg,
        plastic_history=plastic_history,
        redemptions=redemptions,
        pickup_history=pickup_history,
    )
