"""numbers_server.py: an MCP server with three number-theory tools.

  python3 numbers_server.py      (the client starts it; stdio)
The protocol (Algorithm O) is that of ../../ch13/files_server.py; this
file only replaces its tools.  All arithmetic is on Python's exact integers.
"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "ch13"))
import files_server as mcp

def integer(desc, minimum=None):
    s = {"type": "integer", "description": desc}
    if minimum is not None:
        s["minimum"] = minimum
    return s

def tool(name, desc, props):
    return {"name": name, "description": desc,
            "inputSchema": {"type": "object", "properties": props,
                            "required": list(props),
                            "additionalProperties": False},
            "annotations": {"readOnlyHint": True}}

TOOLS = [
    tool("affine_form", "Decide whether n = a*x + b for some integer "
         "x >= 0, and if so return x.",
         {"n": integer("the number to test"),
          "a": integer("the multiplier", 1),
          "b": integer("the constant term")}),
    tool("mod", "Divide n by m: return q and r with n = m*q + r and "
         "0 <= r < m.",
         {"n": integer("the dividend"), "m": integer("the divisor", 1)}),
    tool("is_prime", "Decide whether n is prime; for a composite n, "
         "return its smallest prime factor.",
         {"n": integer("the number to test", 0)}),
]

def get_int(args, key, minimum=None):
    if key not in args:
        raise ValueError(key + " is required")
    v = args[key]
    if isinstance(v, float) and v.is_integer():
        v = int(v)                    # JSON Schema: 5.0 is an integer
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError("%s must be an integer, not %r" % (key, v))
    if minimum is not None and v < minimum:
        raise ValueError("%s must be at least %d" % (key, minimum))
    return v

def affine_form(args):
    n, a, b = get_int(args, "n"), get_int(args, "a", 1), get_int(args, "b")
    x, r = divmod(n - b, a)
    if n < b:
        return "no: n - b = %d is negative, so x < 0" % (n - b)
    if r:
        return "no: n - b = %d = %d*%d + %d, not a multiple of %d" % (
            n - b, a, x, r, a)
    return "yes: x = %d, since %d = %d*%d + %d" % (x, n, a, x, b)

def mod(args):
    n, m = get_int(args, "n"), get_int(args, "m", 1)
    q, r = divmod(n, m)
    return "q = %d, r = %d, since %d = %d*%d + %d" % (q, r, n, m, q, r)

def is_prime(args):
    n = get_int(args, "n", 0)
    if n > 10**14:
        raise ValueError("n must be at most 10**14")
    if n < 2:
        return "no: %d is less than 2" % n
    p = 2 if n % 2 == 0 else next((d for d in range(3, math.isqrt(n) + 1, 2)
                                   if n % d == 0), n)
    if p == n:
        return "yes: %d is prime" % n
    return "no: %d = %d*%d" % (n, p, n // p)

FUNCS = {"affine_form": affine_form, "mod": mod, "is_prime": is_prime}
PARAMS = {t["name"]: t["inputSchema"]["properties"] for t in TOOLS}

def call_tool(name, args):
    if name not in FUNCS:
        raise mcp.RpcError(-32602, "Unknown tool: " + str(name))
    try:
        extra = sorted(set(args) - set(PARAMS[name]))
        if extra:
            raise ValueError("unknown argument: " + ", ".join(extra))
        text, error = FUNCS[name](args), False
    except ValueError as e:            # reported to the model
        text, error = str(e), True
    return {"content": [{"type": "text", "text": text}], "isError": error}

mcp.TOOLS, mcp.call_tool = TOOLS, call_tool
mcp.INFO = {"name": "numbers", "version": "1.0"}

if __name__ == "__main__":
    mcp.main()
