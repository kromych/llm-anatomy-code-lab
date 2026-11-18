# replies.py -- the form of the replies in the lm-eval runs of Chapter 17:
# how many hold the marker #### of GSM8K, how many a \boxed{...}, how many
# neither, and how many of the last kind repeat a line.
# usage: python3 replies.py OUT RESULTS
import glob, json, os, sys
from collections import Counter

RUNS = (("fewshot-Q8_0", "gsm8k"), ("chat-Q8_0", "gsm8k_chat"),
        ("chat-Q4_K_M", "gsm8k_chat"), ("chat-Q4_0", "gsm8k_chat"))

def replies(out, name, task):
    f = glob.glob(f"{out}/lmeval-{name}/*/samples_{task}_*.jsonl")[0]
    rows = [json.loads(l) for l in open(f)]
    return [r["resps"][0][0] for r in rows if r["filter"] == "strict-match"]

def repeats(text, least=20):     # a line of 20 or more characters, twice
    lines = Counter(l.strip() for l in text.split("\n"))
    return any(n > 1 and len(l) >= least for l, n in lines.items())

def main(out, res):
    lines = []
    for name, task in RUNS:
        try:
            texts = replies(out, name, task)
        except IndexError:       # this run was not made
            continue
        marker = ["####" in t for t in texts]
        boxed = ["\\boxed" in t for t in texts]
        neither = [t for t, m, b in zip(texts, marker, boxed)
                   if not (m or b)]
        lines.append(f"{name}: {len(texts)} replies, {sum(marker)} with "
                     f"####, {sum(boxed)} with \\boxed, "
                     f"{sum(m and b for m, b in zip(marker, boxed))} with "
                     f"both, {len(neither)} with neither, of which "
                     f"{sum(map(repeats, neither))} repeat a line")
    os.makedirs(res, exist_ok=True)
    with open(f"{res}/replies.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
