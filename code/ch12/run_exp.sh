#!/bin/sh
# The porting experiment of Chapter 12 from start to end: start the engine
# with one of the two models, put the six questions to every port three
# times through the logging proxy, keep the logs and the versions, make the
# probes that the chapter quotes, and stop the engine. The log that holds
# the requests and replies in full is kept compressed.
#
# Usage: ./run_exp.sh 1.7b|8b OUT          (OUT is a new directory, beside
#                                           this script unless absolute)
#        ./run_exp.sh 1.7b|8b OUT probes   (the probes alone, on the logs
#                                           of OUT, into OUT/probes)
#        python3 analyze.py OUT
# The frameworks live in a virtual environment beside the chapters' code:
#   python3 -m venv ../venv && ../venv/bin/pip install -r requirements.txt
# PY names another interpreter. The engine takes port 8082 and the proxy
# port 8182, both on 127.0.0.1.
set -u
cd "$(dirname "$0")"
case "${1:-}" in
  1.7b) MODEL=ggml-org/Qwen3-1.7B-GGUF:Q4_K_M ;;
  8b)   MODEL=ggml-org/Qwen3-8B-GGUF:Q8_0 ;;
  *)    echo "usage: $0 1.7b|8b OUT [probes]" >&2; exit 2 ;;
esac
OUT=${2:?usage: $0 1.7b|8b OUT [probes]}
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac
if [ "${3:-}" = probes ]; then DIR="$OUT/probes"; else DIR="$OUT"; fi
PY=${PY:-../venv/bin/python}
ENGINE=http://127.0.0.1:8082
PROXY=http://127.0.0.1:8182
BERGEN="What population does cities.csv give for Bergen?"
if [ -e "$DIR" ]; then echo "$DIR exists already" >&2; exit 1; fi
if [ "$DIR" != "$OUT" ] && [ ! -e "$OUT/proxy-full.jsonl.gz" ]; then
  echo "$OUT holds no run" >&2; exit 1
fi
for url in "$ENGINE/health" "$PROXY/check/health"; do
  if curl -s -o /dev/null "$url"; then
    echo "$url answers: the port is taken" >&2; exit 1
  fi
done
mkdir -p "$DIR"

# The ports send no sampling parameters, so the command line of the engine
# carries them.
llama-server -hf "$MODEL" --host 127.0.0.1 --port 8082 \
  --temp 0 --seed 1 --reasoning off -n 1024 > "$DIR/server.log" 2>&1 &
SERVER=$!
trap 'kill $SERVER ${PROXYPID:-} 2>/dev/null; wait' EXIT
trap 'exit 130' INT TERM
until [ "$(curl -s -o /dev/null -w '%{http_code}' "$ENGINE/health")" = 200 ]
do
  if ! kill -0 $SERVER 2>/dev/null; then
    echo "llama-server stopped; see $DIR/server.log" >&2; exit 1
  fi
  sleep 1
done

# What ran: the engine, the model, the packages, the load of the machine.
{ llama-server --version 2>&1
  echo "model: $MODEL"
  "$PY" -c 'import sys
from importlib.metadata import version
print("Python", sys.version.split()[0])
for p in ("smolagents", "pydantic-ai-slim", "openai-agents", "dspy",
          "openai"):
    print(p, version(p))'
  uname -srm
} > "$DIR/versions.txt"
"$PY" -c 'from importlib.metadata import distributions
for line in sorted(f"{d.name}=={d.version}" for d in distributions()):
    print(line)' > "$DIR/packages.txt"
curl -s "$ENGINE/props" > "$DIR/props.json"
uptime > "$DIR/load.txt"

if [ "$DIR" = "$OUT" ]; then
  "$PY" -I proxy.py 8182 "$ENGINE" "$OUT/proxy-run.jsonl" \
    "$OUT/proxy-full.jsonl" > "$OUT/proxy.err" 2>&1 &
  PROXYPID=$!
  sleep 1
  if ! curl -s -f -o /dev/null "$PROXY/check/health"; then
    echo "the proxy does not answer; see $OUT/proxy.err" >&2; exit 1
  fi
  export PYDANTIC_AI_NO_BANNER=1
  for rep in 1 2 3; do
    for p in baseline smolagents pydanticai openai_agents dspy; do
      "$PY" runner.py port_$p "$PROXY/$p-r$rep/v1" "$OUT/results.jsonl" \
        >> "$OUT/runner.log" 2>&1
    done
    echo "rep $rep done"
  done
  uptime >> "$DIR/load.txt"
  kill $PROXYPID; wait $PROXYPID 2>/dev/null
  gzip -9 "$OUT/proxy-full.jsonl"
fi

# The probes, sent to the engine itself after the repetitions: one logged
# request of smolagents again, without the prefix cache and with it; its
# first capped request and its first reply that ended without a call
# again, as logged and changed (see replay.py); and the spans of one
# PydanticAI run.
"$PY" determinism.py "$ENGINE/v1" 4 "$OUT/proxy-full.jsonl.gz" \
  > "$DIR/determinism.txt" 2>&1
"$PY" replay.py "$ENGINE/v1" "$OUT/proxy-full.jsonl.gz" \
  > "$DIR/replay.txt" 2>&1
"$PY" trace_pyd.py "$ENGINE/v1" "$BERGEN" > "$DIR/trace_pyd.txt" 2>&1
uptime >> "$DIR/load.txt"
