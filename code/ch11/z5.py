# z5.py -- step Z5: replace old messages by a summary that the model writes.
import json, urllib.request
import agent, compact

ASK = ("Summarize the conversation below in at most 120 words for an "
       "assistant who will continue it. Keep file names, numbers and "
       "answers that later questions may need.")

def summarize(messages, base, high=2000, low=1200, log=None):
    n = compact.count(messages, base)
    if n <= high:
        return n, 0
    last_user = max(i for i, m in enumerate(messages)
                    if m["role"] == "user")
    old = messages[1:last_user]
    lines = []
    for m in old:
        calls = [c["function"]["name"] + c["function"]["arguments"]
                 for c in m.get("tool_calls", [])]
        lines.append(f"{m['role']}: {m.get('content') or ''} "
                     + (f"[calls {'; '.join(calls)}]" if calls else ""))
    body = {"model": agent.MODEL,
            "messages": [{"role": "system", "content": ASK},
                         {"role": "user", "content": "\n".join(lines)}],
            "temperature": 0, "seed": 1,
            "chat_template_kwargs": {"enable_thinking": False}}
    reply = compact.post(base, "/v1/chat/completions", body)
    if log:
        log(reply)
    summary = reply["choices"][0]["message"]["content"]
    messages[1:last_user] = [{"role": "user", "content":
                              "Summary of our conversation so far: "
                              + summary}]
    return compact.count(messages, base), len(old)
