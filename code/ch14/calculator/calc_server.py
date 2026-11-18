"""calc_server.py: an MCP server with one tool, an exact calculator.

  python3 calc_server.py      (the client starts it; stdio)
The expression is parsed by Python's ast module and evaluated by walking
the tree; eval and exec are never called.  Numbers are exact: integers and
fractions.Fraction.  The protocol is that of ../../ch13/files_server.py.
"""
import ast, decimal, operator, os, sys
from fractions import Fraction
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "ch13"))
import files_server as mcp

MAX_LENGTH = 500          # characters in an expression
MAX_BITS = 10_000         # size of any intermediate numerator/denominator

BINARY = {ast.Add: operator.add, ast.Sub: operator.sub,
          ast.Mult: operator.mul, ast.Div: operator.truediv,
          ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
          ast.Pow: operator.pow}
UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos}

class CalcError(ValueError):
    pass

def number(node):
    v = node.value
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise CalcError("only numbers are allowed, not %r" % (v,))
    if isinstance(v, float):          # 0.1 means exactly 1/10
        if v != v or v in (float("inf"), float("-inf")):
            raise CalcError("number too large: %s" % v)
        v = Fraction(repr(v))
    return Fraction(v)

def check(x):
    if max(x.numerator.bit_length(), x.denominator.bit_length()) > MAX_BITS:
        raise CalcError("a number in the computation is too large")
    return x

def power(x, y):
    if y.denominator != 1:
        raise CalcError("exponents must be integers")
    bits = max(x.numerator.bit_length(), x.denominator.bit_length())
    if bits * abs(y.numerator) > MAX_BITS:
        raise CalcError("the power is too large")
    if x == 0 and y < 0:
        raise CalcError("division by zero")
    return x ** y.numerator

def value(node):
    """Evaluate the tree below node, allowing arithmetic only."""
    if isinstance(node, ast.Constant):
        return number(node)
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY:
        return UNARY[type(node.op)](value(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in BINARY:
        x, y = value(node.left), value(node.right)
        if isinstance(node.op, ast.Pow):
            return check(power(x, y))
        if y == 0 and isinstance(node.op, (ast.Div, ast.FloorDiv,
                                           ast.Mod)):
            raise CalcError("division by zero")
        return check(Fraction(BINARY[type(node.op)](x, y)))
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitXor):
        raise CalcError("^ is not allowed; write ** for a power")
    raise CalcError("not allowed in an expression: "
                    + ast.dump(node).split("(")[0])

def calculate(text):
    if not isinstance(text, str):
        raise CalcError("expression must be a string")
    if len(text) > MAX_LENGTH:
        raise CalcError("expression longer than %d characters" % MAX_LENGTH)
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as e:
        raise CalcError("syntax error: %s" % e.msg) from None
    x = value(tree.body)
    if x.denominator == 1:
        return "%s = %d" % (text, x.numerator)
    with decimal.localcontext() as ctx:
        ctx.prec = 30
        approx = decimal.Decimal(x.numerator) / x.denominator
    return "%s = %s (about %s)" % (text, x, approx)

TOOLS = [{
    "name": "calculate",
    "description": "Evaluate an arithmetic expression exactly. Allowed: "
                   "integers, decimals, + - * / // % ** and parentheses. "
                   "Results are exact integers or fractions.",
    "inputSchema": {"type": "object", "additionalProperties": False,
                    "properties": {"expression": {
                        "type": "string", "maxLength": MAX_LENGTH,
                        "description": "for example (12345 * 6789) // 7"}},
                    "required": ["expression"]},
    "annotations": {"readOnlyHint": True, "openWorldHint": False}}]

def call_tool(name, args):
    if name != "calculate":
        raise mcp.RpcError(-32602, "Unknown tool: " + str(name))
    try:
        if "expression" not in args:
            raise CalcError("expression is required")
        extra = sorted(set(args) - {"expression"})
        if extra:
            raise CalcError("unknown argument: " + ", ".join(extra))
        text, error = calculate(args.get("expression")), False
    except CalcError as e:              # reported to the model
        text, error = str(e), True
    return {"content": [{"type": "text", "text": text}], "isError": error}

mcp.TOOLS, mcp.call_tool = TOOLS, call_tool
mcp.INFO = {"name": "calculator", "version": "1.0"}

if __name__ == "__main__":
    mcp.main()
