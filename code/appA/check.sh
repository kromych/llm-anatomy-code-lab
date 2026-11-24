#!/bin/sh
# check.sh -- compare installed tool versions with the pins in versions.csv
# (Appendix A).  Read-only: it runs each tool's version command and changes
# nothing.  Tools that are absent are reported as "missing".
#   ./check.sh                       # tools on PATH
#   VENV=~/venv ./check.sh           # also the packages of one environment
here=$(cd "$(dirname "$0")" && pwd)
csv=${1:-$here/versions.csv}
[ -n "${VENV:-}" ] && PATH="$VENV/bin:$PATH" && export PATH
printf '%-38s %-10s %-10s %s\n' tool pinned found status
tail -n +2 "$csv" | while IFS=, read -r group tool pinned where date pat unix win
do
  [ -z "$unix" ] && continue
  if out=$(sh -c "$unix" 2>&1 </dev/null); then
    ver=$(printf '%s\n' "$out" | grep -Eo "${pat:-[0-9]+(\.[0-9]+)+}" |
          head -n 1 | tr -cd '0-9.')
  else
    ver=
  fi
  want=$(printf '%s' "$pinned" | tr -cd '0-9.')
  if [ -z "$ver" ]; then status=missing; ver=-
  elif [ "$ver" = "$want" ]; then status=ok
  else status=differs
  fi
  printf '%-38s %-10s %-10s %s\n' "$tool" "$pinned" "$ver" "$status"
done
