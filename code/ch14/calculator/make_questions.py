"""make_questions.py: write questions.json, 12 arithmetic questions.

Multi-digit products, nested parentheses, large powers and fractions;
the expected values are computed here with exact arithmetic.
"""
import json
from fractions import Fraction as F

EXPRESSIONS = [
    ("48271 * 69621", F(48271) * 69621),
    ("987654321 * 123456789", F(987654321) * 123456789),
    ("(123 + 456) * (789 - 1011) + 31415",
     F(123 + 456) * (789 - 1011) + 31415),
    ("((17 * 23) - (19 * 29)) * ((31 + 37) * 41)",
     F((17 * 23) - (19 * 29)) * ((31 + 37) * 41)),
    ("2 ** 64", F(2) ** 64),
    ("3 ** 40", F(3) ** 40),
    ("999999 * 999999 - 1", F(999999) * 999999 - 1),
    ("(2 ** 31 - 1) * (2 ** 31 + 1)", F(2 ** 31 - 1) * (2 ** 31 + 1)),
    ("123456789 // 4567", F(123456789 // 4567)),
    ("1/3 + 2/7 - 5/11", F(1, 3) + F(2, 7) - F(5, 11)),
    ("(3/4) ** 5 * 1024", F(3, 4) ** 5 * 1024),
    ("355/113 - 22/7", F(355, 113) - F(22, 7)),
]

qs = []
for i, (e, v) in enumerate(EXPRESSIONS, 1):
    qs.append({"id": "c%02d" % i, "expression": e,
               "expected": {"value": str(v)},
               "question": ("Compute %s exactly. End your reply with one "
                            "line 'ANSWER: <value>', giving an integer or "
                            "a fraction p/q in lowest terms." % e)})
json.dump(qs, open("questions.json", "w"), indent=1)
for q in qs:
    print(q["id"], q["expression"], "=", q["expected"]["value"])
