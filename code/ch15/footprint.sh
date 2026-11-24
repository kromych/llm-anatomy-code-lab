#!/bin/sh
# footprint.sh DIR: record what a harness has left on this Mac (names and
# sizes only, never file contents) so two snapshots can be diffed.
out=$1; mkdir -p "$out"
brew list --versions > "$out/brew.txt" 2>/dev/null
for d in "$HOME" "$HOME/.config" "$HOME/.local/share" "$HOME/.local/state" \
         "$HOME/.cache" "$HOME/Library/Application Support" \
         "$HOME/Library/Caches" "$HOME/Library/Preferences" \
         "$HOME/Library/LaunchAgents"; do
  [ -d "$d" ] && ls -A "$d" | sed "s|^|$d/|"
done | sed "s|^$HOME|~|" > "$out/entries.txt"
lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null |
  awk 'NR>1 {print $1, $9}' | sort -u > "$out/listening.txt"
launchctl list 2>/dev/null | awk 'NR>1 {print $3}' | sort > "$out/launchd.txt"
