#!/bin/bash
# stop.sh NAME -- stop the server that serve.sh started under that name
cd /tmp/scratch
pid=$(cat run/$1.pid) && kill $pid && while kill -0 $pid 2>/dev/null; do sleep 0.5; done
rm -f run/$1.pid; nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr '\n' ' '; echo
