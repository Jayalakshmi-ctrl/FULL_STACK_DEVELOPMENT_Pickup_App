import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class PickupStatus(str, enum.Enum):
    requested = "Requested"
    picked_up = "Picked Up"


class Pickup(Base):
    __tablename__ = "pickups"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_email: Mapped[str] = mapped_column(String(320), index=True)
    address: Mapped[str] = mapped_column(String(500))
    pickup_date: Mapped[date] = mapped_column(Date)
    # VARCHAR avoids PostgreSQL ENUM issues across schema versions ("Requested" / "Picked Up").
    status: Mapped[str] = mapped_column(String(32), default=PickupStatus.requested.value, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class EcoWallet(Base):
    __tablename__ = "eco_wallets"

    customer_email: Mapped[str] = mapped_column(String(320), primary_key=True)
    eco_points_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PlasticVerification(Base):
    __tablename__ = "plastic_verifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_email: Mapped[str] = mapped_column(String(320), index=True)
    customer_email: Mapped[str] = mapped_column(String(320), index=True)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    eco_points_awarded: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RewardType(str, enum.Enum):
    sapling = "sapling"
    organic_seeds = "organic_seeds"
    compost = "compost"


class PhysicalReward(Base):
    __tablename__ = "physical_rewards"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    reward_type: Mapped[RewardType] = mapped_column(Enum(RewardType))
    description: Mapped[str] = mapped_column(String(500))
    points_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(default=True)


class RedemptionStatus(str, enum.Enum):
    requested = "requested"
    fulfilled = "fulfilled"


class Redemption(Base):
    __tablename__ = "redemptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_email: Mapped[str] = mapped_column(String(320), index=True)
    reward_id: Mapped[int] = mapped_column(ForeignKey("physical_rewards.id"), index=True)
    points_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RedemptionStatus] = mapped_column(Enum(RedemptionStatus), default=RedemptionStatus.requested)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reward: Mapped["PhysicalReward"] = relationship()

