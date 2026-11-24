# judge.py -- position bias of a model used as a judge. For each GSM8K
# question on which the sampled runs produced both a right and a wrong
# solution, ask the judge which of the two is right, in both orders.
# usage: python3 judge.py BASE_URL NAME LOG...  (Inspect logs of gsm.py)
import json, re, sys, urllib.request
from inspect_ai.log import read_eval_log

ASK = ("Below are a math word problem and two solutions, A and B. Exactly "
       "one of them reaches the correct final answer. Which one? Reply "
       "with the single letter A or B.\n\nProblem: {q}\n\n"
       "Solution A:\n{a}\n\nSolution B:\n{b}\n")

def pairs(logs):
    found = {}                       # sample id -> (question, right, wrong)
    for path in logs:
        log = read_eval_log(path, resolve_attachments=True)
        for s in log.samples:
            q, text = s.input, s.output.completion
            ok = s.scores["last_number_match"].value == "C"
            right, wrong = found.get(s.id, (q, None, None))[1:]
            if ok and right is None:
                right = text
            if not ok and wrong is None:
                wrong = text
            found[s.id] = (q, right, wrong)
    return [(i, *v) for i, v in sorted(found.items()) if None not in v]

def verdict(base, q, a, b):
    body = {"messages": [{"role": "user",
                          "content": ASK.format(q=q, a=a, b=b)}],
            "temperature": 0, "max_tokens": 16,
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(base + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        text = json.load(r)["choices"][0]["message"]["content"] or ""
    m = re.search(r"\b([AB])\b", text.strip())
    return m.group(1) if m else "?"

if __name__ == "__main__":
    base, name, logs = sys.argv[1], sys.argv[2], sys.argv[3:]
    for i, q, right, wrong in pairs(logs):
        first = verdict(base, q, right, wrong)     # right solution is A
        second = verdict(base, q, wrong, right)    # right solution is B
        print(json.dumps({"judge": name, "id": i, "right_first": first,
                          "right_second": second}), flush=True)
