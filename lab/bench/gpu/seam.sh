#!/bin/bash
# seam.sh NAME PORT MODEL -- the probes of Chapters 9 and 10 against a
# server on the loopback interface; one record per program.
name=$1; port=$2; model=$3
cd /tmp/scratch; out=rec/seam/$name; mkdir -p $out
c9=supplement/code/ch09/scripts; c10=supplement/code/ch10/scripts
base=http://127.0.0.1:$port
probe() {  # probe FILE COMMAND...: record the command and what it prints
  f=$out/$1; shift
  { echo "## $*" | sed "s|supplement/code/ch[0-9]*/scripts/||"; timeout 900 "$@" 2>&1; } > $f
  echo "$(basename $f): $(wc -l < $f) lines"
}
probe conform16.txt   python3 $c10/conform.py $base/v1 $model
probe status.txt      python3 $c9/status.py $base/v1 $model
probe toolchoice.txt  python3 $c9/toolchoice.py $base/v1 $model
probe parallel.txt    python3 $c9/parallel.py $base/v1 $model
probe reasoning.txt   python3 $c9/reasoning.py $base/v1 $model
probe endpoints.txt   python3 $c10/endpoints.py $base $model
probe origin.txt      python3 $c10/origin.py $base
probe determinism.txt python3 $c10/determinism.py $base/v1 $model
