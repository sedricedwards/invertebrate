#!/usr/bin/env bash
# Copies the fixture, then generates 30 distractor views that call the unrelated dates.format().
set -eu
cp -R "$(dirname "$0")/files/." .
mkdir -p src/views
for i in $(seq 1 30); do
  printf 'import { format } from "../dates";\n\nexport const view%s = (d: Date) => "Updated " + format(d);\n' "$i" > "src/views/view$i.ts"
done
