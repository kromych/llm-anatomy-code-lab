"""One question, typed output, PydanticAI and the Agents SDK; dump requests.

Usage: python3 output_typed.py PROXY   (for example http://127.0.0.1:8182)
An engine that reads the model name, such as Ollama, gets it from the
environment variable AGENT_MODEL.
"""
import asyncio, os, sys
from pydantic import BaseModel
import common

class City(BaseModel):
    city: str
    population: int

Q = "Which Norwegian city in cities.csv has the largest population?"
MODEL = os.environ.get("AGENT_MODEL", "local")

def pyd(base):
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider
    m = OpenAIChatModel(MODEL, provider=OpenAIProvider(base_url=base, api_key="none"))
    a = Agent(m, instructions=common.SYSTEM, output_type=City,
              tools=[common.list_files, common.read_file, common.calculate])
    return a.run_sync(Q).output

def oai(base):
    from agents import (Agent, OpenAIChatCompletionsModel, Runner,
                        function_tool, set_tracing_disabled)
    from openai import AsyncOpenAI
    set_tracing_disabled(True)
    m = OpenAIChatCompletionsModel(model=MODEL,
        openai_client=AsyncOpenAI(base_url=base, api_key="none"))
    a = Agent(name="workspace", instructions=common.SYSTEM, model=m, output_type=City,
              tools=[function_tool(f) for f in (common.list_files, common.read_file, common.calculate)])
    return Runner.run_sync(a, Q, max_turns=10).final_output

for name, f in (("pydanticai", pyd), ("openai_agents", oai)):
    try:
        print(name, repr(f(f"{sys.argv[1]}/{name}-out-dump/v1")))
    except Exception as e:
        print(name, "ERROR", type(e).__name__, str(e)[:300])
