#!/bin/sh
# footprint_linux.sh DIR: the Linux counterpart of footprint.sh.  Records
# what a harness has left in the home directory (names only, never file
# contents), user services, cron, listening sockets and global npm
# packages, so that two snapshots can be diffed.
out=$1; mkdir -p "$out"
for d in "$HOME" "$HOME/.config" "$HOME/.local/share" "$HOME/.local/state" \
         "$HOME/.local/bin" "$HOME/.cache"; do
  [ -d "$d" ] && ls -A "$d" | sed "s|^|$d/|"
done | sed "s|^$HOME|~|" > "$out/entries.txt"
systemctl --user list-unit-files --no-legend 2>/dev/null |
  awk '{print $1, $2}' | sort > "$out/user-units.txt"
crontab -l 2>/dev/null | grep -v '^#' > "$out/crontab.txt"
ss -ltnH 2>/dev/null | awk '{print $4}' | sort -u > "$out/listening.txt"
npm ls -g --depth=0 2>/dev/null | sed 1d > "$out/npm-global.txt"
