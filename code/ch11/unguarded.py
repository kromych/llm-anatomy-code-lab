# unguarded.py -- the loop of agent.py, as it stands, on a server that
# limits each reply (llama-server -n 20, then -n 8): what becomes of a
# tool call that the limit cuts off.  Usage: python3 unguarded.py BASE
import json, sys, urllib.error
import agent

reasons = []
try:
    answer, messages = agent.run(
        "What does docs/formats.md say about GGUF?", sys.argv[1],
        log=lambda turn, reply: reasons.append(
            reply["choices"][0]["finish_reason"]))
    print("answer:", repr(answer))
except urllib.error.HTTPError as e:
    print("request", len(reasons) + 1, "raised:", e, json.load(e))
print("finish reasons:", *reasons)
