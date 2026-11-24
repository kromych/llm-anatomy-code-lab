# session.py -- a twelve-question conversation; logs tokens per request.
import json, sys, time
import agent, compact

QUESTIONS = [
    "What does docs/formats.md say about GGUF?",
    "Summarize docs/serving.md in one sentence.",
    "What is the first sentence of docs/agents.md?",
    "How many lines of log/server.log contain ERROR?",
    "Which request numbers failed, according to log/server.log?",
    "Which port does config/server.toml set?",
    "Does docs/formats.md mention safetensors?",
    "Read docs/serving.md again and give me its title.",
    "List all files in the workspace.",
    "What is the total of the gigabytes column of data/sizes.csv?",
    "Which file defines dequantize?",
    "Read docs/agents.md again and tell me its title.",
]

def session(base, compacting):
    msgs = [{"role": "system", "content": agent.SYSTEM}]
    rows = []
    for q, question in enumerate(QUESTIONS):
        msgs.append({"role": "user", "content": question})
        for turn in range(6):
            n, elided = (compact.compact(msgs, base, 2000, 1200) if compacting
                         else (None, 0))
            t0 = time.time()
            reply = agent.chat(msgs, base)
            u, t = reply["usage"], reply.get("timings", {})
            rows.append(dict(question=q + 1, request=len(rows) + 1,
                             counted=n, elided=elided,
                             prompt=u["prompt_tokens"],
                             cached=u["prompt_tokens_details"][
                                 "cached_tokens"],
                             computed=t.get("prompt_n"),
                             prompt_ms=t.get("prompt_ms"),
                             completion=u["completion_tokens"],
                             seconds=round(time.time() - t0, 3)))
            msg = reply["choices"][0]["message"]
            calls = msg.get("tool_calls") or []
            msgs.append({"role": "assistant", "content": msg.get("content"),
                         **({"tool_calls": calls} if calls else {})})
            if not calls:
                rows[-1]["answer"] = (msg.get("content") or "")[:80]
                break
            for c in calls:
                out = agent.call(c["function"]["name"],
                                 c["function"]["arguments"])
                msgs.append({"role": "tool", "tool_call_id": c["id"],
                             "content": agent.clip(out)})
    return rows

if __name__ == "__main__":
    for row in session(sys.argv[1], sys.argv[2] == "compact"):
        print(json.dumps(row))
