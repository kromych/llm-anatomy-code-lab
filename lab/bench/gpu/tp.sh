#!/bin/bash
# tp.sh NAME GPUS TP MODEL SERVED EXTRA... -- vllm serve with tensor
# parallelism TP on the given GPUs; records the processes, the memory of
# the GPUs, and a short sweep of the concurrency; then stops the server.
name=$1; gpus=$2; tp=$3; model=$4; served=$5; shift 5
cd /tmp/scratch
bin/serve.sh $name $gpus 8000 $model --served-model-name $served \
    --tensor-parallel-size $tp "$@" || exit 1
pstree -a -p -T $(cat run/$name.pid) | cut -c1-150 > rec/vllm/$name.ps.txt
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader > rec/vllm/$name.gpus.txt
MIN_N=8 bin/sweep.sh $name 8000 $model $served 512 256 "${CS:-1 16 64}"
bin/stop.sh $name > /dev/null
