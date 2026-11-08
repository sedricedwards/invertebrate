#!/usr/bin/env bash
# Real-world case: files/ holds an upstream project with the PR applied, and files/pr.diff is the PR.
# Rebuild the pre-PR state as one commit (no history that would point at the bug), then re-apply the PR uncommitted.
set -eu
src="$(dirname "$0")/files"
cp -R "$src/." .
git init -q -b main
git apply -R pr.diff
git add -A
git reset -q -- pr.diff pr_description.md
git -c user.name=dev -c user.email=dev@example.com commit -q -m "Import upstream"
git apply pr.diff
