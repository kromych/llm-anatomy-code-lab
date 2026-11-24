# rag.py EMBED_BASE CHAT_BASE DOCUMENT QUESTIONS [K] -- retrieval end to
# end: cut a Markdown document into passages, find the passages nearest
# to each question with embed.py, and let a chat model answer without
# them and with the best K, three unless K is given.  QUESTIONS holds a
# question, a tab, and a string that a right answer contains, on each
# line.  Standard library only.
import json, sys, urllib.request
from embed import embed, rank

def passages_of(text, limit):
    """Blocks between blank lines, cut at line ends to LIMIT characters;
    each passage begins with the heading it stands under."""
    out, heading = [], ""
    for block in text.split("\n\n"):
        lines = [line for line in block.split("\n") if line.strip()]
        if lines and lines[0].startswith("#"):
            heading = lines.pop(0).lstrip("# ")
        piece = ""
        for line in lines:
            if piece and len(piece) + len(line) > limit:
                out.append(heading + "\n" + piece)
                piece = ""
            piece += line[:limit] + "\n"
        if piece:
            out.append(heading + "\n" + piece)
    return out

def vectors_of(base, passages, batch=16):
    return [v for i in range(0, len(passages), batch)
            for v in embed(base, passages[i:i + batch])]

def answer(base, question, found):
    system = "Answer in one short sentence."
    if found:
        system += (" Take the answer from these passages of the "
                   "documentation:\n\n" + "\n---\n".join(found))
    body = {"model": "chat", "temperature": 0, "max_tokens": 100,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": question}],
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(base + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    reply = json.load(urllib.request.urlopen(req, timeout=300))
    return (reply["choices"][0]["message"]["content"],
            reply["usage"]["prompt_tokens"])

embed_base, chat_base = sys.argv[1], sys.argv[2]
text = open(sys.argv[3]).read()
questions = [line.rstrip("\n").split("\t") for line in open(sys.argv[4])]
K = int(sys.argv[5]) if len(sys.argv) > 5 else 3
print(f"{len(text)} characters, {len(questions)} questions")
print(f"passages of at most  passages  first holds answer  one of {K}")
for limit in (300, 600, 1200, 2400):
    passages = passages_of(text, limit)
    vectors = vectors_of(embed_base, passages)
    first = three = 0
    for question, expect in questions:
        found = [p for _, p in rank(embed_base, question, passages,
                                    vectors, K)]
        first += expect in found[0]
        three += any(expect in p for p in found)
    print(f"{limit:8} characters {len(passages):9} {first:15} {three:15}")
    if limit == 600:
        kept = passages, vectors

passages, vectors = kept
right = {False: 0, True: 0}
tokens = {False: 0, True: 0}
for question, expect in questions:
    found = [p for _, p in rank(embed_base, question, passages, vectors,
                                K)]
    for use in (False, True):
        reply, n = answer(chat_base, question, found if use else [])
        right[use] += expect in reply
        tokens[use] += n
    print(("ok   " if expect in reply else "MISS ") + question[:44],
          "->", reply.replace("\n", " ")[:22])
for use, label in ((False, "without passages"), (True, f"with {K}")):
    print(f"{label:17} {right[use]:2} of {len(questions)} right, "
          f"{tokens[use] / len(questions):.0f} prompt tokens a question")
