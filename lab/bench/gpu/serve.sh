#!/bin/bash
# serve.sh NAME GPUS PORT ARGS... -- start `vllm serve ARGS` on the given
# GPUs, wait until /health answers 200, and print the seconds that took.
name=$1; gpus=$2; port=$3; shift 3
cd /tmp/scratch; mkdir -p run rec/vllm
export HF_HOME=/tmp/scratch/hf PATH=/tmp/scratch/venv-vllm/bin:$PATH
log=rec/vllm/$name.server.log
echo "## CUDA_VISIBLE_DEVICES=$gpus vllm serve $*" > $log
t0=$(date +%s.%N)
CUDA_VISIBLE_DEVICES=$gpus nohup venv-vllm/bin/vllm serve "$@" \
    --host 127.0.0.1 --port $port >> $log 2>&1 &
echo $! > run/$name.pid
for i in $(seq 1 1800); do
  if [ "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:$port/health)" = 200 ]; then
    t1=$(date +%s.%N); echo "$name ready after $(echo "$t1 - $t0" | bc) s"; exit 0
  fi
  kill -0 $(cat run/$name.pid) 2>/dev/null || { echo "$name died"; tail -5 $log; exit 1; }
  sleep 0.5
done
echo "$name not ready after 900 s"; exit 1
