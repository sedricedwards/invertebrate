#!/usr/bin/env bash
# Builds a git history in which the guard removed by pr.diff was added by a bug-fix commit,
# then leaves the PR's post-change files uncommitted in the working tree.
set -eu
src="$(dirname "$0")/files"
cp -R "$src/." .
c() { git -c user.name=dev -c user.email=dev@example.com commit -q "$@"; }
git init -q -b main
# v1: original code without the guard
cat > app/billing.py <<'PY'
from app.gateway import capture


def charge(order):
    capture(order.payment_id, order.total_cents)
    order.charged = True
    order.save()
PY
git add -A
git reset -q -- pr.diff pr_description.md
c -m "Add billing and payment webhook"
# v2: the fix
cat > app/billing.py <<'PY'
from app.gateway import capture


def charge(order):
    if order.charged:
        return
    capture(order.payment_id, order.total_cents)
    order.charged = True
    order.save()
PY
git add app/billing.py
c -m "Fix double charge when payment webhook is retried (#41)"
# PR state: guard removed again, uncommitted
cp "$src/app/billing.py" app/billing.py
