import json, sys
import compact, session, z5
extra = []
def log(reply):
    u, t = reply["usage"], reply.get("timings", {})
    extra.append(dict(prompt=u["prompt_tokens"], cached=u["prompt_tokens_details"]["cached_tokens"],
                      computed=t.get("prompt_n"), completion=u["completion_tokens"],
                      prompt_ms=t.get("prompt_ms"), summary=reply["choices"][0]["message"]["content"]))
compact.compact = lambda m, b, h, l: z5.summarize(m, b, h, l, log)
for row in session.session(sys.argv[1], True):
    print(json.dumps(row))
for e in extra:
    print(json.dumps({"summary_request": e}))
