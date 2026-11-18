#!/bin/bash
# every 5 s: total CPU busy (top) and processes other than the benchmark above 20% of a core
out=$1
while :; do
  top -l 2 -n 15 -o cpu -s 5 -stats pid,cpu,command 2>/dev/null | awk -v t="$(date +%T)" '
    /^CPU usage/ {n++; if (n==2) {gsub("%","",$7); print t, "0 TOTAL_BUSY%", 100-$7}}
    n==2 && $1 ~ /^[0-9]+$/ && $2+0 > 20 && $3 !~ /^(llama-bench|top)$/ {print t, $1, $3, $2/100}' >> $out
done
