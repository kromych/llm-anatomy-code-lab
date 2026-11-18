#!/bin/sh
# Run the battery under each sandbox named on the command line
# (Chapter 16).  Mechanisms: none seatbelt seatbelt-exec codex srt
# bwrap landlock seccomp docker podman runsc.  Everything the run
# creates lives in one directory under $HOME, which is removed at
# the end.  With TIMES=n, time n starts of `true` under each sandbox
# instead.  SRT and RUNSC give the commands for srt and runsc where
# they are not on PATH, e.g. SRT="npx -y @anthropic-ai/sandbox-runtime".
set -u
here=$(cd "$(dirname "$0")" && pwd)
root=$(mktemp -d "$HOME/.battery-sbx.XXXXXX")         # not under /tmp
mkdir -p "$root/work/.git/hooks" "$root/outside" "$root/secret"
echo dummy-token-not-a-real-secret > "$root/secret/token.txt"
python3 "$here/listener.py" "$root/port" "$root/log" &
listener=$!
trap '{ kill $listener; wait; } 2>/dev/null; rm -rf "$root"' EXIT
while [ ! -s "$root/port" ]; do sleep 0.1; done
port=$(cat "$root/port")
py=$(command -v python3)
battery="$py $here/battery.py $root $port"
inner="python3 $here/battery.py $root $port"      # in a container
image=docker.io/library/python:3.13-alpine
time=
if [ -n "${TIMES:-}" ]; then
  time="$py $here/timeit.py $TIMES"
  battery=$(command -v true) inner=true
fi

for mech in "$@"; do
  : > "$root/log"
  rm -f "$root/work/ok.txt" "$root/outside/probe.txt" \
    "$root/work/.git/hooks/pre-commit" "$root/work/orphan.txt"
  echo "== $mech"
  case $mech in
  none) $time $battery ;;
  seatbelt)
    $time sandbox-exec -f "$here/battery.sb" -D WORK="$root/work" \
      -D GIT="$root/work/.git" -D SECRET="$root/secret" $battery ;;
  seatbelt-exec)                   # exec only the Python interpreter
    prefix=$($py -c 'import os,sys; print(os.path.realpath(sys.prefix))')
    rule='(allow process-fork) (allow process-exec (subpath (param "PY")))'
    sed "s/^(allow process-fork process-exec)/$rule/" "$here/battery.sb" \
      > "$root/exec.sb"
    $time sandbox-exec -f "$root/exec.sb" -D WORK="$root/work" \
      -D GIT="$root/work/.git" -D SECRET="$root/secret" \
      -D PY="$prefix" $battery ;;
  codex)                           # Codex CLI's built-in :workspace
    mkdir -p "$root/codex-home"
    CODEX_HOME="$root/codex-home" $time codex sandbox -P :workspace \
      -C "$root/work" -- $battery ;;
  srt)                             # Anthropic's sandbox runtime
    cat > "$root/srt.json" <<EOF
{"network": {"allowedDomains": [], "deniedDomains": []},
 "filesystem": {"denyRead": ["$root/secret"], "allowRead": [],
                "allowWrite": ["$root/work"], "denyWrite": []}}
EOF
    (cd "$root/work" &&
      $time ${SRT:-srt} --settings "$root/srt.json" $battery) ;;
  bwrap)
    $time bwrap --ro-bind / / --dev /dev --proc /proc \
      --bind "$root/work" "$root/work" --tmpfs "$root/secret" \
      --ro-bind "$root/work/.git" "$root/work/.git" \
      --unshare-all --die-with-parent --new-session -- $battery ;;
  landlock)
    $time $py "$here/landlock.py" --ro /usr --ro /etc --ro "$here" \
      --rw "$root/work" -- $battery ;;
  seccomp)
    cc -O2 -o "$root/nonet" "$here/nonet.c" &&
      $time "$root/nonet" $battery ;;
  docker|podman)                   # rootless podman: keep our uid
    [ $mech = podman ] && keep=--userns=keep-id || keep=
    $time $mech run --rm $keep --network none --read-only --cap-drop ALL \
      --security-opt no-new-privileges --user "$(id -u):$(id -g)" \
      -v "$root/work:$root/work:z" -v "$here:$here:ro,z" \
      $image $inner ;;
  runsc)                           # gVisor; every write stays in RAM
    $time "${RUNSC:-runsc}" --rootless --network=none do $battery ;;
  esac
  [ -n "$time" ] && continue
  sleep 3                          # time for an orphan to leave its mark
  [ -e "$root/work/ok.txt" ] && c=yes || c=no
  [ -e "$root/outside/probe.txt" ] && w=yes || w=no
  [ -e "$root/work/.git/hooks/pre-commit" ] && h=yes || h=no
  [ -e "$root/work/orphan.txt" ] && o=yes || o=no
  echo "   on the host: ok.txt $c, probe.txt $w, pre-commit $h," \
       "orphan.txt $o, connections $(wc -l < "$root/log" | tr -d ' ')"
done
