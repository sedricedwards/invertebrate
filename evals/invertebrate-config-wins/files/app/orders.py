from app.db import ORDERS
from app.audit import audit_log


def update_address(user, order_id, address):
    """Change the shipping address of an order the user owns."""
    order = ORDERS[order_id]
    if order["owner"] != user:
        raise PermissionError("not your order")
    order["address"] = address
    audit_log(user, "update_address", order_id)
    return order


def cancel_order(user, order_id):
    order = ORDERS[order_id]
    order["status"] = "cancelled"
    return order
