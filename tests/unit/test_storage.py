import pytest

from cafe_order_kiosk.kiosk_store import KioskStore
from cafe_order_kiosk.models import OrderStatus


def test_create_order_and_add_items_total() -> None:
    store = KioskStore.with_default_menu()
    order = store.create_order(note="hot")

    store.add_item(order.id, menu_item_id=1, quantity=2, options=["ice"])
    store.add_item(order.id, menu_item_id=2, quantity=1)

    order = store.get_order(order.id)
    assert order is not None
    assert order.total == 3500 * 2 + 4000
    assert order.status is OrderStatus.OPEN


def test_remove_item_updates_total() -> None:
    store = KioskStore.with_default_menu()
    order = store.create_order()

    store.add_item(order.id, menu_item_id=1, quantity=1)
    store.add_item(order.id, menu_item_id=2, quantity=1)
    store.remove_item(order.id, line_index=1)

    order = store.get_order(order.id)
    assert order is not None
    assert order.total == 4000


def test_pay_order_success() -> None:
    store = KioskStore.with_default_menu()
    order = store.create_order()

    store.add_item(order.id, menu_item_id=1, quantity=1)
    store.pay_order(order.id, method="card", amount=3500)

    order = store.get_order(order.id)
    assert order is not None
    assert order.status is OrderStatus.PAID
    assert order.payment is not None
    assert order.payment.method == "card"


def test_pay_order_amount_mismatch() -> None:
    store = KioskStore.with_default_menu()
    order = store.create_order()

    store.add_item(order.id, menu_item_id=1, quantity=1)

    with pytest.raises(ValueError, match="Payment amount does not match final total"):
        store.pay_order(order.id, method="card", amount=1000)


def test_cancel_paid_order_is_error() -> None:
    store = KioskStore.with_default_menu()
    order = store.create_order()

    store.add_item(order.id, menu_item_id=1, quantity=1)
    store.pay_order(order.id, method="card", amount=3500)

    with pytest.raises(ValueError, match="Paid order cannot be canceled"):
        store.cancel_order(order.id)
