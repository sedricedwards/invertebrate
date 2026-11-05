def capture(payment_id, amount_cents):
    """Capture funds. Not idempotent: every call moves money."""
    raise NotImplementedError("real gateway call")
