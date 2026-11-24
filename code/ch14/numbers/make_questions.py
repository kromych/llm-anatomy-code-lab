"""make_questions.py: write questions.json, 20 affine-form questions.

Ten have the answer yes and ten no; n has 7 or 8 digits.  Twelve use
a = 7, b = 7987789; eight use other forms.  The expected answers are
computed here with exact integers.
"""
import json

B = 7987789
FORMS = [  # (n, a, b); odd entries match, even entries do not
    (7988601, 7, B), (8000000, 7, B),
    (8123456, 7, B), (8123457, 7, B),
    (7987789, 7, B), (7987000, 7, B),
    (9876543, 7, B), (9876544, 7, B),
    (B + 7 * 622841, 7, B), (B + 7 * 622841 + 3, 7, B),
    (B + 7 * 6795395, 7, B), (B + 7 * 6795395 + 1, 7, B),
    (5000000 + 11 * 17, 11, 5000000), (5000000 + 11 * 17 + 7, 11, 5000000),
    (1000003 + 13 * 76543, 13, 1000003),
    (1000003 + 13 * 76543 + 6, 13, 1000003),
    (12345678 + 97 * 4321, 97, 12345678),
    (12345678 + 97 * 4321 - 1, 97, 12345678),
    (2024 + 1001 * 9999, 1001, 2024),
    (2024 + 1001 * 9999 + 500, 1001, 2024),
]

def expected(n, a, b):
    x, r = divmod(n - b, a)
    ok = n >= b and r == 0
    return {"matches": ok, "x": x if ok else None}

qs = []
for i, (n, a, b) in enumerate(FORMS, 1):
    qs.append({"id": "n%02d" % i, "n": n, "a": a, "b": b,
               "expected": expected(n, a, b),
               "question": ("Is %d of the form %d*x + %d for some integer "
                            "x >= 0? If it is, find x. End your reply with "
                            "one line, either 'ANSWER: yes, x = <x>' or "
                            "'ANSWER: no'." % (n, a, b))})
json.dump(qs, open("questions.json", "w"), indent=1)
print(sum(q["expected"]["matches"] for q in qs), "yes of", len(qs))
for q in qs:
    print(q["id"], q["n"], q["a"], q["b"], q["expected"])
