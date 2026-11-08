# #12 Password reset by email

Users who forget their password need a way back in.

Acceptance criteria:
- `create_reset_token(user_id)` returns a random token; only a hash of it is stored.
- A token expires 1 hour after it is created.
- A token is single-use: after a successful reset it must no longer work.

Open question: should we also email the user when their password changes? (not for this ticket)
