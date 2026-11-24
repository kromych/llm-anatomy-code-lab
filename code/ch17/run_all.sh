#!/bin/sh
# run_all.sh -- the measurements of Chapter 17, one after another, against
# llama-server on port $PORT (8086). Needs lm_eval and inspect in $VENV and the
# Gemma 3 1B GGUF files in $MODELS. Raw logs go to $OUT.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
VENV=${VENV:-venv}; MODELS=${MODELS:-$HOME/models/gemma-3-1b-it}
OUT=${OUT:-out}; PORT=${PORT:-8086}; mkdir -p "$OUT"
# llama-server reads LLAMA_API_KEY itself, so Inspect gets another name.
export LOCAL_BASE_URL=http://127.0.0.1:$PORT/v1 LOCAL_API_KEY=none
MODEL_ARGS=model=gemma,base_url=$LOCAL_BASE_URL/chat/completions
MODEL_ARGS=$MODEL_ARGS,num_concurrent=8

serve() {  # serve QUANT SLOTS [server options]
  q=$1; np=$2; shift 2
  pkill -f "llama-server.*--port $PORT" ; sleep 1
  llama-server -m "$MODELS/google_gemma-3-1b-it-$q.gguf" --port $PORT \
      -c $((4096 * np)) -np "$np" "$@" > "$OUT/server-$q-$np${1:-}.log" 2>&1 &
  until curl -sf 127.0.0.1:$PORT/health > /dev/null; do sleep 1; done
}
lmeval() {  # lmeval TASK NAME [extra args]; skipped if done before
  task=$1; name=$2; shift 2
  [ -d "$OUT/lmeval-$name" ] && return
  "$VENV/bin/lm_eval" --model local-chat-completions \
    --model_args "$MODEL_ARGS" \
    --include_path "$HERE/tasks" --tasks "$task" --apply_chat_template \
    --log_samples --output_path "$OUT/lmeval-$name" "$@" \
    > "$OUT/lmeval-$name.log" 2>&1
}
inspect() {  # inspect NAME CONNECTIONS [generate options]
  name=$1; conns=$2; shift 2
  [ -d "$OUT/inspect-$name" ] && return
  "$VENV/bin/inspect" eval "$HERE/gsm.py" --model openai-api/local/gemma \
    --max-connections "$conns" --log-dir "$OUT/inspect-$name" \
    --max-tokens 768 --display none "$@" > "$OUT/inspect-$name.log" 2>&1
}

serve Q8_0 8
lmeval gsm8k_chat chat-Q8_0
lmeval gsm8k fewshot-Q8_0 --fewshot_as_multiturn
for r in 1 2 3 4 5; do inspect t0-serial-$r 1 --temperature 0; done
for r in 1 2 3 4 5; do inspect t0-parallel-$r 8 --temperature 0; done
for s in 1 2 3 4 5 6 7 8 9 10; do
  inspect t07-seed-$s 8 --temperature 0.7 --seed $s; done
inspect t07-seed-1-again 8 --temperature 0.7 --seed 1
serve Q8_0 8 --no-cache-prompt     # is the prompt cache what varies?
for r in 1 2 3; do inspect t0-serial-nocache-$r 1 --temperature 0; done
serve Q4_0 8; lmeval gsm8k_chat chat-Q4_0
serve Q4_K_M 8; lmeval gsm8k_chat chat-Q4_K_M
pkill -f "llama-server.*--port $PORT"
