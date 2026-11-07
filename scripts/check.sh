#!/bin/sh
# Run the unit tests and the Markdown link checks.
# Usage: sh scripts/check.sh
set -u

cd "$(dirname "$0")/.." || exit 1

if [ "$#" -gt 0 ]; then
  printf 'Usage: sh scripts/check.sh\n' >&2
  exit 2
fi

status=0

printf 'Unit tests\n'
if python3 -m unittest; then
  unit=passed
else
  unit=failed
  status=1
fi

printf '\nMarkdown links\n'
if python3 scripts/check_markdown_links.py; then
  links=passed
else
  links=failed
  status=1
fi

printf '\nSummary\n'
printf '  unit tests: %s\n' "$unit"
printf '  markdown links: %s\n' "$links"
if [ "$status" -eq 0 ]; then
  printf 'OK\n'
else
  printf 'Failed\n'
fi
exit "$status"
