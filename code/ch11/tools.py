# tools.py -- a tool registry; each function's signature becomes its schema.
import ast, inspect, operator, pathlib

ROOT = pathlib.Path("ws").resolve()       # the only directory tools may use
TOOLS = {}                                # name -> (function, schema)
TYPES = {str: "string", int: "integer", float: "number", bool: "boolean"}

def tool(fn):
    sig = inspect.signature(fn)
    props = {n: {"type": TYPES[p.annotation]}
             for n, p in sig.parameters.items()}
    need = [n for n, p in sig.parameters.items() if p.default is p.empty]
    TOOLS[fn.__name__] = (fn, {"type": "function", "function": {
        "name": fn.__name__, "description": inspect.getdoc(fn),
        "parameters": {"type": "object", "properties": props,
                       "required": need}}})
    return fn

def inside(path):
    p = (ROOT / path).resolve()
    if not p.is_relative_to(ROOT):
        raise PermissionError(f"{path} is outside the workspace")
    return p

@tool
def list_files(directory: str = ".") -> str:
    """List the files below a directory of the workspace."""
    d = inside(directory)
    return "\n".join(sorted(p.relative_to(ROOT).as_posix()
                            for p in d.rglob("*") if p.is_file()))

@tool
def read_file(path: str) -> str:
    """Return the text of a file in the workspace."""
    return inside(path).read_text(encoding="utf-8", errors="replace")

@tool
def search(text: str) -> str:
    """Return the lines of workspace files that contain the text."""
    hits = []
    for name in list_files().splitlines():
        for i, line in enumerate(read_file(name).splitlines(), 1):
            if text in line:
                hits.append(f"{name}:{i}: {line}")
    return "\n".join(hits) or "no matches"

OPS = {ast.Add: operator.add, ast.Sub: operator.sub,
       ast.Mult: operator.mul, ast.Div: operator.truediv,
       ast.USub: operator.neg}

@tool
def calc(expression: str) -> float:
    """Evaluate arithmetic with numbers, + - * / and parentheses."""
    def ev(n):
        if isinstance(n, ast.BinOp):
            return OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp):
            return OPS[type(n.op)](ev(n.operand))
        if isinstance(n, ast.Constant) and type(n.value) in (int, float):
            return n.value
        raise ValueError("only numbers and + - * / are allowed")
    return ev(ast.parse(expression, mode="eval").body)
