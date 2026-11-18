#!/bin/sh
# snapshot.sh DIR -- record, in DIR, the places an installer may change, so
# that two snapshots can be compared with `diff -r BEFORE AFTER`. Names and
# checksums only, never file contents. macOS and Linux.
#
#   sh snapshot.sh /tmp/snap-before
#   ... install, run, remove ...
#   sh snapshot.sh /tmp/snap-after
#   diff -r /tmp/snap-before /tmp/snap-after
#
# The snapshots list your whole home directory's top level and your
# services; keep them to yourself and publish only the differences.
out=$1
[ -n "$out" ] || { echo "usage: $0 DIR" >&2; exit 2; }
mkdir -p "$out"
os=$(uname -s)

# the directories to list, one per line: a name may hold spaces, and so may
# the path of the home directory
dirs() {
  printf '%s\n' "$HOME" "$HOME/.config" "$HOME/.local/share" \
    "$HOME/.local/state" "$HOME/.local/bin" "$HOME/.cache"
  if [ "$os" = Darwin ]; then
    L=$HOME/Library
    printf '%s\n' "$L/Application Support" "$L/Caches" "$L/Preferences" \
      "$L/Logs" "$L/LaunchAgents" "$L/HTTPStorages" \
      "$L/Saved Application State" /Applications /Library/LaunchAgents \
      /Library/LaunchDaemons /usr/local/bin /opt/homebrew/bin
  else
    printf '%s\n' "$HOME/.config/systemd/user" /usr/local/bin \
      /usr/local/lib /usr/local/share /opt /etc/systemd/system \
      /etc/profile.d
  fi
}

# top-level entries of each directory, the home directory written as ~
dirs | while IFS= read -r d; do
  [ -d "$d" ] || continue
  case $d in
    "$HOME")   p='~' ;;
    "$HOME"/*) p="~${d#"$HOME"}" ;;
    *)         p=$d ;;
  esac
  ls -A "$d" 2>/dev/null | while IFS= read -r e; do
    printf '%s/%s\n' "$p" "$e"
  done
done | sort > "$out/entries.txt"

# shell start-up files: a checksum each, to see whether an installer
# edited one (compare the files themselves privately if a checksum changes)
for f in .profile .bashrc .bash_profile .zshrc .zprofile .zshenv; do
  [ -f "$HOME/$f" ] && printf '%s %s\n' \
    "$(cksum < "$HOME/$f" | cut -d' ' -f1)" "~/$f"
done > "$out/profiles.txt"

if [ "$os" = Darwin ]; then
  lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null |
    awk 'NR>1 {print $1, $9}' | sort -u > "$out/listening.txt"
  launchctl list 2>/dev/null | awk 'NR>1 {print $3}' |
    sed -E 's/(\.[0-9]+)+$//' | sort -u > "$out/services.txt"
  command -v brew >/dev/null &&
    brew list --versions > "$out/packages.txt" 2>/dev/null
else
  ss -ltnH 2>/dev/null | awk '{print $4}' | sort -u > "$out/listening.txt"
  { systemctl list-unit-files --state=enabled --no-legend 2>/dev/null |
      awk '{print "system", $1}'
    systemctl --user list-unit-files --state=enabled --no-legend \
      2>/dev/null | awk '{print "user", $1}'
    systemctl --user list-units --state=running --no-legend 2>/dev/null |
      awk '{print "user-running", $1}'
  } | sort > "$out/services.txt"
  getent passwd | cut -d: -f1 | sort > "$out/users.txt"
  command -v docker >/dev/null &&
    docker image ls --format '{{.Repository}}:{{.Tag}} {{.Size}}' \
      2>/dev/null | sort > "$out/images.txt"
fi
echo "snapshot in $out"
