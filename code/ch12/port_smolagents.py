from smolagents import OpenAIServerModel, ToolCallingAgent, tool
import common

def make(base_url):
    model = OpenAIServerModel(model_id="local", api_base=base_url,
                              api_key="none")
    agent = ToolCallingAgent(
        tools=[tool(f) for f in (common.list_files, common.read_file,
                                 common.calculate)],
        model=model, instructions=common.SYSTEM, max_steps=10,
        verbosity_level=0)
    return lambda question: str(agent.run(question, reset=True))
