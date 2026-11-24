#!/bin/sh
# run_harnesses.sh OUT ROUND [HARNESS...]: give the Chapter 15 task to each
# harness in turn, every one pointed at the logging proxy (proxy.py), and
# record the outcome.  The proxy must listen on $PROXY and forward to an
# OpenAI-compatible engine that serves the model under the name $MODEL.
#   python3 proxy.py 8184 http://127.0.0.1:8084 log.jsonl dumps/
PROXY=${PROXY:-http://127.0.0.1:8184}
MODEL=${MODEL:-qwen3-8b}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$1" && OUT=$(cd "$1" && pwd); ROUND=$2; shift 2
HARNESSES=${*:-codex opencode goose aider openhands}
PROMPT='Fix the bug in stats.py so that `python3 -m unittest` passes.'
PROMPT="$PROMPT Do not change the tests."

fresh() {    # a new git repository holding the task
  cp -R "$HERE/task" "$1" && cd "$1" && git init -q &&
  printf '__pycache__/\n' > .git/info/exclude && git add -A &&
  git -c user.name=t -c user.email=t@example.invalid commit -qm task
}

for h in $HARNESSES; do
  tag=$h-$ROUND; dir=$OUT/$tag; base=$PROXY/$tag/v1
  fresh "$dir" || exit 1
  t0=$(date +%s)
  case $h in
  codex)
    timeout 1200 codex exec -s workspace-write -c model_provider=local \
      -c model="$MODEL" -c 'model_providers.local.name="local"' \
      -c "model_providers.local.base_url=\"$base\"" \
      -c 'model_providers.local.wire_api="responses"' "$PROMPT" ;;
  opencode)
    OPENCODE_CONFIG_CONTENT=$(printf '{"provider": {"local%s": {
      "npm": "@ai-sdk/openai-compatible", "options": {"baseURL": "%s"},
      "models": {"%s": {"limit": {"context": 40960, "output": 8192}}}}},
      "autoupdate": false, "share": "disabled"}' \
      "$ROUND" "$base" "$MODEL") \
    timeout 1200 opencode run --standalone --auto --archived \
      --format json -m "local$ROUND/$MODEL" "$PROMPT" ;;
  goose)
    GOOSE_PROVIDER=openai GOOSE_MODEL=$MODEL OPENAI_API_KEY=local \
    OPENAI_HOST=$PROXY/$tag OPENAI_BASE_PATH=v1/chat/completions \
    GOOSE_MODE=auto GOOSE_DISABLE_KEYRING=1 GOOSE_TELEMETRY_OFF=1 \
    GOOSE_CONTEXT_LIMIT=40960 \
    timeout 1200 goose run -n "$tag" --max-turns 30 \
      --output-format stream-json -t "$PROMPT" ;;
  aider)
    timeout 1200 aider --model "openai/$MODEL" --openai-api-base "$base" \
      --openai-api-key local --yes-always --no-check-update \
      --analytics-disable --no-show-model-warnings --no-pretty --no-stream \
      --test-cmd 'python3 -m unittest' --auto-test --message "$PROMPT" ;;
  openhands)
    LLM_MODEL=openai/$MODEL LLM_BASE_URL=$base LLM_API_KEY=local \
    OPENHANDS_SUPPRESS_BANNER=1 \
    timeout 1200 openhands --headless --json --override-with-envs \
      -t "$PROMPT" ;;
  esac > "$OUT/$tag.out" 2> "$OUT/$tag.err" < /dev/null
  rc=$?
  tests=fail; python3 -m unittest > /dev/null 2>&1 && tests=pass
  kept=no; git diff --quiet "$(git rev-list --max-parents=0 HEAD)" \
    -- test_stats.py && kept=yes
  secs=$(( $(date +%s) - t0 ))
  echo "$tag rc=$rc secs=$secs tests=$tests tests_kept=$kept" |
    tee -a "$OUT/outcomes.txt"
done
