from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
import common

def make(base_url):
    model = OpenAIChatModel("local", provider=OpenAIProvider(
        base_url=base_url, api_key="none"))
    agent = Agent(model, instructions=common.SYSTEM,
                  tools=[common.list_files, common.read_file,
                         common.calculate])
    return lambda question: agent.run_sync(question).output
