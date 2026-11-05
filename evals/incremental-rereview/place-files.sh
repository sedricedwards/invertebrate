#!/usr/bin/env bash
# Builds: main (Account) -> feature commit A (withdraw, overdraft bug; reviewed in prior_review.md)
#         -> feature commit B (fixes overdraft, adds transfer() that loses money if dst is frozen).
set -eu
c() { git -c user.name=dev -c user.email=dev@example.com commit -q "$@"; }
git init -q -b main
mkdir -p app
touch app/__init__.py
cat > app/accounts.py <<'PY'
class Frozen(Exception):
    pass


class Account:
    def __init__(self, balance=0, frozen=False):
        self.balance = balance
        self.frozen = frozen

    def credit(self, amount):
        if self.frozen:
            raise Frozen()
        self.balance += amount
PY
git add -A && c -m "Account model"
git checkout -q -b feature
cat >> app/accounts.py <<'PY'


def withdraw(acct, amount):
    acct.balance -= amount
PY
git add -A && c -m "Add withdraw"
sha_a=$(git rev-parse HEAD)
cat > prior_review.md <<MD
## Invertebrate Review — feature

### Summary
Adds withdraw(). It never checks the balance, so accounts can go negative.

### Confidence Score: 3/5
One P1 overdraft bug.

### Findings
| # | Sev | Type | Proof | Location | Issue |
|---|---|---|---|---|---|
| 1 | P1 | logic | repro | \`app/accounts.py:17\` | withdraw() allows overdraft |

### Inline Comments

#### 1. [P1 · logic] withdraw() allows overdraft
\`app/accounts.py:17\`

withdraw(Account(balance=5), 10) leaves balance at -5. Reject amounts above the balance.

---
<sub>Reviewed 1 files · config: defaults · strictness 2 · ${sha_a:0:7}</sub>
<!-- invertebrate:sha=${sha_a} -->
MD
head -n 15 app/accounts.py > app/accounts.tmp
cat >> app/accounts.tmp <<'PY'
def withdraw(acct, amount):
    if amount > acct.balance:
        raise ValueError("insufficient funds")
    acct.balance -= amount


def transfer(src, dst, amount):
    withdraw(src, amount)
    dst.credit(amount)
PY
mv app/accounts.tmp app/accounts.py
git add app/accounts.py && c -m "Reject overdraft; add transfer"
