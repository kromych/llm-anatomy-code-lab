# guard.py -- step N2 at the server's limits: compact when the prompt
# exceeds the window, and ask again when the token limit cuts a reply.
import json, urllib.error
import agent, compact

def chat(messages, base, limit):
    body = {"model": agent.MODEL, "messages": messages, "temperature": 0,
            "seed": 1, "max_tokens": limit,
            "tools": [schema for _, schema in agent.TOOLS.values()],
            "chat_template_kwargs": {"enable_thinking": False}}
    return compact.post(base, "/v1/chat/completions", body)

def guarded(messages, base=agent.BASE, limit=512, most=4096):
    while True:
        try:
            reply = chat(messages, base, limit)
        except urllib.error.HTTPError as e:
            error = json.load(e).get("error", {}) if e.code == 400 else {}
            if error.get("type") != "exceed_context_size_error":
                raise
            sent, window = error["n_prompt_tokens"], error["n_ctx"]
            n, elided = compact.compact(messages, base, 0, window // 2)
            if not elided:               # nothing to elide: step Z5
                raise
            print(f"[{sent} tokens exceed the window of {window}; "
                  f"elided {elided}, left {n}]")
            continue
        if reply["choices"][0].get("finish_reason") != "length":
            return reply
        if limit >= most:
            raise RuntimeError(f"no complete reply in {limit} tokens")
        print(f"[reply cut off at {limit} tokens; asking again]")
        limit *= 2                       # the cut reply is dropped
