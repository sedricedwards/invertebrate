# Simplify naturalday/naturaldate

Remove the timezone branches; both functions convert to a plain `date` anyway, so comparing against `date.today()` is enough.
