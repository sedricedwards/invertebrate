from app.gateway import capture


def charge(order):
    capture(order.payment_id, order.total_cents)
    order.charged = True
    order.save()
