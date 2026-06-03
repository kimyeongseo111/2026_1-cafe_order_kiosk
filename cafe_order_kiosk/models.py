from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from cafe_order_kiosk.utils import utc_now


class OrderStatus(str, Enum):
    OPEN = "open"
    PAID = "paid"
    CANCELED = "canceled"


class DiscountKind(str, Enum):
    FIXED = "fixed"
    PERCENT = "percent"


@dataclass(frozen=True)
class MenuItem:
    id: int
    name: str
    price: int
    category: str | None = None
    description: str | None = None
    is_available: bool = True


@dataclass
class OrderItem:
    menu_item_id: int
    name: str
    unit_price: int
    quantity: int
    options: list[str] = field(default_factory=list)

    @property
    def line_total(self) -> int:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class Payment:
    method: str
    amount: int
    paid_at: datetime


@dataclass(frozen=True)
class Coupon:
    code: str
    kind: DiscountKind
    value: int

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("Coupon code is required")
        if self.kind is DiscountKind.PERCENT:
            if not 1 <= self.value <= 100:
                raise ValueError("Percent discount must be between 1 and 100")
        elif self.value < 1:
            raise ValueError("Fixed discount must be at least 1")

    def calculate_discount(self, subtotal: int) -> int:
        """쿠폰 종류에 맞춰 할인 금액을 계산합니다. 할인은 주문 금액을 넘지 않습니다."""
        if self.kind is DiscountKind.PERCENT:
            discount = subtotal * self.value // 100
        else:
            discount = self.value
        return min(discount, subtotal)


@dataclass
class Order:
    id: int
    items: list[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.OPEN
    created_at: datetime = field(default_factory=utc_now)
    paid_at: datetime | None = None
    canceled_at: datetime | None = None
    note: str | None = None
    payment: Payment | None = None
    coupon: Coupon | None = None

    @property
    def total(self) -> int:
        return sum(item.line_total for item in self.items)

    @property
    def discount_amount(self) -> int:
        if self.coupon is None:
            return 0
        return self.coupon.calculate_discount(self.total)

    @property
    def final_total(self) -> int:
        """할인을 뺀 최종 결제 금액입니다."""
        return self.total - self.discount_amount
