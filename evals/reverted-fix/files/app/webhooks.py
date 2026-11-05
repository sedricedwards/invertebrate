from app.billing import charge
from app.orders import get_order


def on_payment_authorized(event):
    # The provider retries this webhook until it gets a 200, so it can arrive more than once.
    charge(get_order(event["order_id"]))
    return 200
