#!/bin/sh
# run_more.sh -- the second half of the measurements of Chapter 17: the
# engine swap (one GGUF file in Ollama and in llama-server), the agent of
# Chapter 11 under Inspect, and two judges. Run after run_all.sh, with
# Ollama serving and its model gemma3:1b pulled.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
VENV=${VENV:-venv}; OUT=${OUT:-out}; PORT=${PORT:-8086}; mkdir -p "$OUT"
export LOCAL_BASE_URL=http://127.0.0.1:$PORT/v1 LOCAL_API_KEY=none
HF=$HOME/.cache/huggingface/hub
QWEN17=$(ls $HF/models--ggml-org--Qwen3-1.7B-GGUF/snapshots/*/*Q4_K_M.gguf)
QWEN8=$(ls $HF/models--ggml-org--Qwen3-8B-GGUF/snapshots/*/*Q8_0.gguf)
BLOB=$(ollama show --modelfile gemma3:1b | sed -n 's/^FROM //p')

serve() {  # serve FILE SLOTS NAME
  pkill -f "llama-server.*--port $PORT" ; sleep 1
  llama-server -m "$1" --port $PORT -c $((8192 * $2)) -np "$2" \
      > "$OUT/server-$3.log" 2>&1 &
  until curl -sf 127.0.0.1:$PORT/health > /dev/null; do sleep 1; done
}

# 1. the same weights in two engines, temperature 0: Ollama first (this
# command is restored from the header of the stored log), then llama-server
# with the file that Ollama keeps for the model
"$VENV/bin/inspect" eval "$HERE/gsm.py" --model ollama/gemma3:1b \
  --temperature 0 --max-tokens 768 --max-connections 4 \
  --log-dir "$OUT/inspect-ollama-t0-1" --display none
serve "$BLOB" 1 ollama-blob
"$VENV/bin/inspect" eval "$HERE/gsm.py" --model openai-api/local/gemma \
  --temperature 0 --max-tokens 768 --max-connections 4 \
  --log-dir "$OUT/inspect-blob-t0-1" --display none

# 2. our agent, without and with the hint, five epochs at 0.7
serve "$QWEN17" 1 qwen17
for h in false true; do
  "$VENV/bin/inspect" eval "$HERE/agent_eval.py" --model none \
    -T temperature=0.7 -T hint=$h --epochs 5 \
    --log-dir "$OUT/agent-hint-$h" --display none
done

# 3. two judges on pairs of right and wrong solutions, each on a server of
# its own; the 8B judge runs twice, to see whether its verdicts repeat
LOGS=$(ls "$OUT"/inspect-t07-seed-*/*.eval | grep -v again)
serve "$QWEN17" 1 qwen17-judge
"$VENV/bin/python" "$HERE/judge.py" "$LOCAL_BASE_URL" qwen3-1.7b $LOGS \
  > "$OUT/judge-qwen3-1.7b.jsonl"
serve "$QWEN8" 1 qwen8
for run in "" -again; do
  "$VENV/bin/python" "$HERE/judge.py" "$LOCAL_BASE_URL" qwen3-8b $LOGS \
    > "$OUT/judge-qwen3-8b$run.jsonl"
done
pkill -f "llama-server.*--port $PORT"
