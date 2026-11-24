from openai import AsyncOpenAI
from agents import (Agent, OpenAIChatCompletionsModel, Runner,
                    function_tool, set_tracing_disabled)
import common

set_tracing_disabled(True)

def make(base_url):
    client = AsyncOpenAI(base_url=base_url, api_key="none")
    model = OpenAIChatCompletionsModel(model="local", openai_client=client)
    agent = Agent(name="workspace", instructions=common.SYSTEM, model=model,
                  tools=[function_tool(f) for f in (common.list_files,
                         common.read_file, common.calculate)])
    return lambda question: Runner.run_sync(agent, question,
                                            max_turns=10).final_output
