from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class PickupCreateIn(BaseModel):
    address: str = Field(min_length=5, max_length=500)
    pickup_date: date


class PickupOut(BaseModel):
    id: int
    customer_email: str
    address: str
    pickup_date: date
    status: str
    created_at: datetime
    updated_at: datetime | None = None


class PickupStatusUpdateIn(BaseModel):
    status: str
    weight_kg: float | None = Field(default=None, gt=0, le=500)
    notes: str | None = Field(default=None, max_length=500)


class RewardHistoryItem(BaseModel):
    pickup_id: int
    pickup_date: date
    status: str
    points_earned: int
    created_at: datetime
    updated_at: datetime | None = None


class PlasticVerificationOut(BaseModel):
    id: int
    weight_kg: float
    eco_points_awarded: int
    vendor_email: str
    created_at: datetime
    notes: str | None = None


class RedemptionHistoryItem(BaseModel):
    id: int
    reward_name: str
    reward_type: str
    points_spent: int
    status: str
    delivery_date: date | None = None
    sent_at: datetime | None = None
    created_at: datetime


class RewardsOut(BaseModel):
    eco_points_balance: int
    eco_points_per_kg: int
    plastic_history: list[PlasticVerificationOut]
    redemptions: list[RedemptionHistoryItem]
    pickup_history: list[RewardHistoryItem]


class VerifyPlasticIn(BaseModel):
    customer_email: EmailStr
    weight_kg: float = Field(gt=0, le=500)
    notes: str | None = Field(default=None, max_length=500)


class VerifyPlasticOut(BaseModel):
    id: int
    customer_email: str
    weight_kg: float
    eco_points_awarded: int
    vendor_email: str
    new_balance: int
    created_at: datetime


class PhysicalRewardOut(BaseModel):
    id: int
    slug: str
    name: str
    reward_type: str
    description: str
    points_cost: int


class RedeemIn(BaseModel):
    reward_id: int


class RedeemOut(BaseModel):
    id: int
    reward_name: str
    points_spent: int
    remaining_balance: int
    status: str
    delivery_date: date | None = None
    sent_at: datetime | None = None
    created_at: datetime


class AdminRedemptionOut(BaseModel):
    id: int
    customer_email: str
    reward_name: str
    reward_type: str
    points_spent: int
    status: str
    delivery_date: date | None = None
    sent_at: datetime | None = None
    created_at: datetime


class ScheduleDeliveryIn(BaseModel):
    delivery_date: date


class WalletOut(BaseModel):
    customer_email: str
    eco_points_balance: int
