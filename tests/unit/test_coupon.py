import pytest

from cafe_order_kiosk.kiosk_store import KioskStore
from cafe_order_kiosk.models import Coupon, DiscountKind, Order


def _order_with_item(store: KioskStore, menu_item_id: int, quantity: int) -> Order:
    order = store.create_order()
    store.add_item(order.id, menu_item_id=menu_item_id, quantity=quantity)
    return order


def test_apply_and_remove_coupon() -> None:
    store = KioskStore.with_default_menu()
    order = _order_with_item(store, 1, 2)

    store.apply_coupon(order.id, " welcome ")
    assert order.coupon is not None
    assert order.coupon.code == "WELCOME"
    assert order.discount_amount == 700
    assert order.final_total == 6300

    store.remove_coupon(order.id)
    assert order.coupon is None
    assert order.final_total == order.total == 7000


def test_payment_uses_discounted_total() -> None:
    store = KioskStore.with_default_menu()
    order = _order_with_item(store, 1, 1)
    store.apply_coupon(order.id, "WELCOME")

    with pytest.raises(ValueError, match="does not match"):
        store.pay_order(order.id, method="card", amount=3500)

    store.pay_order(order.id, method="card", amount=3150)
    assert order.payment is not None
    assert order.payment.amount == 3150


def test_coupon_value_must_be_valid() -> None:
    with pytest.raises(ValueError, match="between 1 and 100"):
        Coupon(code="X", kind=DiscountKind.PERCENT, value=0)


def test_fixed_discount_cannot_exceed_total() -> None:
    coupon = Coupon(code="BIG", kind=DiscountKind.FIXED, value=100000)
    assert coupon.calculate_discount(3500) == 3500


def test_unknown_coupon_is_rejected() -> None:
    store = KioskStore.with_default_menu()
    order = _order_with_item(store, 1, 1)

    with pytest.raises(ValueError, match="Coupon not found"):
        store.apply_coupon(order.id, "NOPE")

    assert order.coupon is None
