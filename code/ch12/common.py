"""Tools, tasks and grading shared by every port of the agent."""
import ast, operator, pathlib, re

WORKSPACE = pathlib.Path(__file__).parent / "workspace"

def list_files() -> str:
    """List the names of the files in the workspace, one per line."""
    return "\n".join(sorted(p.name for p in WORKSPACE.iterdir()))

def read_file(name: str) -> str:
    """Return the contents of one file of the workspace.

    Args:
        name: the file name, as returned by list_files.
    """
    path = WORKSPACE / pathlib.Path(name).name
    if not path.is_file():
        return f"error: no file named {name!r}"
    return path.read_text()

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.USub: operator.neg}

def calculate(expression: str) -> str:
    """Evaluate an arithmetic expression with + - * / and parentheses.

    Args:
        expression: for example "700000 + 290000".
    """
    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.operand))
        raise ValueError("unsupported expression")
    try:
        return str(ev(ast.parse(expression, mode="eval").body))
    except Exception as e:  # report errors to the model as text
        return f"error: {e}"

SYSTEM = ("You answer questions about the files in a small workspace. "
          "Use the tools to look at the files; give a short final answer.")

TASKS = [
    ("files", "How many files are in the workspace?", ["4"]),
    ("bergen", "What population does cities.csv give for Bergen?", ["290000"]),
    ("deadline", "Which file mentions a deadline? Answer with the file name.",
     ["notes.txt"]),
    ("norway", "What is the total population of the Norwegian cities in "
     "cities.csv?", ["1200000", "1.2 million"]),
    ("errors", "How many lines of log.txt contain the word ERROR?", ["3"]),
    ("todo", "What is the first item in todo.md?", ["renew passport"]),
]

def correct(answer: str, expected: list[str]) -> bool:
    a = re.sub(r"(?<=\d)[,\s](?=\d{3})", "", (answer or "").lower())
    for e in expected:
        for m in re.finditer(r"(?<![\w.])" + re.escape(e) + r"(?!\w)", a):
            # a number at the start of a line followed by "." or ")" is the
            # marker of a numbered list, not an answer
            line_start = a.rfind("\n", 0, m.start()) + 1
            if (e[0].isdigit() and not a[line_start:m.start()].strip(" *#-")
                    and a[m.end():m.end() + 1] in (".", ")")):
                continue
            return True
    return False
