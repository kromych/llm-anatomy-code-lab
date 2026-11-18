# schema2.py -- schemas for lists, fixed choices and optional parameters.
import inspect, types, typing
from tools import TOOLS, TYPES

def schema_of(t):
    origin, args = typing.get_origin(t), typing.get_args(t)
    if origin is list:
        return {"type": "array", "items": schema_of(args[0])}
    if origin is typing.Literal:
        return {"enum": list(args)}
    if origin in (typing.Union, types.UnionType):
        rest = [a for a in args if a is not type(None)]
        return {"anyOf": [schema_of(a) for a in rest] + [{"type": "null"}]}
    return {"type": TYPES[t]}

def parameters(fn):
    props, need = {}, []
    for n, p in inspect.signature(fn).parameters.items():
        props[n] = schema_of(p.annotation)
        if p.default is p.empty:
            need.append(n)
        else:
            props[n]["default"] = p.default
    return {"type": "object", "properties": props, "required": need}

def tool(fn):
    TOOLS[fn.__name__] = (fn, {"type": "function", "function": {
        "name": fn.__name__, "description": inspect.getdoc(fn),
        "parameters": parameters(fn)}})
    return fn
