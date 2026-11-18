# exp_guard.py -- the session of session.py behind guard.py, for a server
# whose window is smaller than the session needs, such as
#   llama-server -hf ggml-org/Qwen3-1.7B-GGUF:Q4_K_M -c 2048 -np 1
# Usage: python3 exp_guard.py BASE [LIMIT]
import functools, json, sys
import agent, guard, session

limit = int(sys.argv[2]) if len(sys.argv) > 2 else 512
agent.chat = functools.partial(guard.guarded, limit=limit)
for row in session.session(sys.argv[1], False):
    print(json.dumps({k: row.get(k) for k in (
        "question", "request", "prompt", "cached", "completion",
        "answer")}))
