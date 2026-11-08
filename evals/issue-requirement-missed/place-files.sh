#!/usr/bin/env bash
# The store and users modules exist on main; app/reset.py is the PR, uncommitted.
set -eu
src="$(dirname "$0")/files"
cp -R "$src/." .
git init -q -b main
git add app/__init__.py app/store.py app/users.py
git -c user.name=dev -c user.email=dev@example.com commit -q -m "Add user store"
