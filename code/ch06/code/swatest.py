# swatest.py URL [REPLIES] -- what llama-server reuses of a prompt after a
# long answer has moved the windows of a model with sliding-window layers
# (Gemma 3). URL is the base of the seam, e.g. http://127.0.0.1:8080/v1;
# the replies are appended to the file REPLIES as JSON lines.
import json, sys, urllib.request

URL = sys.argv[1] + "/chat/completions"
doc = " ".join(f"Item {i} costs {i * 7 % 100} euros." for i in range(800))
head = [{"role": "system", "content": "Answer from this list: " + doc}]

def ask(label, messages, n):
    body = {"max_tokens": n, "temperature": 0, "messages": head + messages}
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        reply = json.load(resp)
    if len(sys.argv) > 2:
        with open(sys.argv[2], "a") as f:
            f.write(json.dumps({"request": label, "reply": reply}) + "\n")
    t = reply["timings"]
    print(f"{label:9s} from cache {t['cache_n']:5d}   computed "
          f"{t['prompt_n']:5d}   generated {t['predicted_n']:5d}")
    return reply["choices"][0]["message"]

copy = {"role": "user", "content": "Copy the list, one item per line."}
which = {"role": "user", "content": "Which item costs 42 euros?"}
answer = ask("first", [copy], 2400)          # a long answer
ask("extended", [copy, answer, which], 32)   # the next turn
ask("repeated", [copy], 32)                  # the answer is regenerated
ask("edited", [which], 32)                   # the question is replaced
