#!/bin/sh
# run_linux.sh -- run the transport benchmarks on a shared Linux lab host.
# Waits (up to 4 h) until the host's other workload releases its heavy lock
# and the load is low, then holds that lock while measuring, so that the
# two never overlap. Writes results/<host>-rtt.csv and results/<host>-mmap.csv.
#   sh run_linux.sh MODEL.gguf [LOCKFILE]
cd "$(dirname "$0")"
MODEL=$1; LOCK=${2:-$HOME/.badc-heavy.lock}; H=$(hostname -s)
mkdir -p results
end=$(( $(date +%s) + 14400 ))
while :; do
  load=$(cut -d' ' -f1 /proc/loadavg)
  if [ "$(echo "$load < 1.5" | bc)" = 1 ]; then
    flock -w 600 "$LOCK" sh -c "
      echo start \$(date +%T) load \$(cut -d' ' -f1 /proc/loadavg)
      venv/bin/python rtt.py -n 5000 --only call,ctypes,shm,stdio,unix,mpconn,tcp,zmq,http,dbus,ollama > results/$H-rtt.csv
      venv/bin/python mmap_pagein.py '$MODEL' -k 2000 > results/$H-mmap.csv
      echo done \$(date +%T) load \$(cut -d' ' -f1 /proc/loadavg)
    " && exit 0
  fi
  [ "$(date +%s)" -gt "$end" ] && { echo "gave up, load $load"; exit 1; }
  sleep 30
done
