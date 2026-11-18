import json, typing
from schema2 import tool, TOOLS

@tool
def grep(pattern: str, files: list[str],
         mode: typing.Literal["plain", "regex"] = "plain",
         limit: int | None = None) -> str:
    """Return the lines of the files that match the pattern."""

print(json.dumps(TOOLS["grep"][1]["function"]["parameters"]))
