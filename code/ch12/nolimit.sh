#!/bin/sh
# What the limit of generated tokens is for: start the engine as
# run_exp.sh does but without -n 1024, send to it again the first request
# of smolagents that the limit had cut off in a run (replay.py), and stop
# the engine.
#
# Usage: ./nolimit.sh 1.7b|8b RUN      (writes RUN/nolimit/)
set -u
cd "$(dirname "$0")"
case "${1:-}" in
  1.7b) MODEL=ggml-org/Qwen3-1.7B-GGUF:Q4_K_M ;;
  8b)   MODEL=ggml-org/Qwen3-8B-GGUF:Q8_0 ;;
  *)    echo "usage: $0 1.7b|8b RUN" >&2; exit 2 ;;
esac
RUN=${2:?usage: $0 1.7b|8b RUN}
case "$RUN" in /*) ;; *) RUN="$PWD/$RUN" ;; esac
DIR="$RUN/nolimit"
ENGINE=http://127.0.0.1:8082
if [ -e "$DIR" ]; then echo "$DIR exists already" >&2; exit 1; fi
if curl -s -o /dev/null "$ENGINE/health"; then
  echo "port 8082 is taken" >&2; exit 1
fi
mkdir -p "$DIR"
llama-server -hf "$MODEL" --host 127.0.0.1 --port 8082 \
  --temp 0 --seed 1 --reasoning off > "$DIR/server.log" 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null; wait' EXIT
trap 'exit 130' INT TERM
until [ "$(curl -s -o /dev/null -w '%{http_code}' "$ENGINE/health")" = 200 ]
do
  if ! kill -0 $SERVER 2>/dev/null; then
    echo "llama-server stopped; see $DIR/server.log" >&2; exit 1
  fi
  sleep 1
done
{ llama-server --version 2>&1; echo "model: $MODEL"; } > "$DIR/versions.txt"
curl -s "$ENGINE/props" > "$DIR/props.json"
python3 replay.py "$ENGINE/v1" "$RUN/proxy-full.jsonl.gz" capped \
  > "$DIR/replay.txt" 2>&1
