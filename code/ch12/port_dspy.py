import dspy
import common

def make(base_url):
    lm = dspy.LM("openai/local", api_base=base_url, api_key="none",
                 temperature=0, max_tokens=1024, cache=False,
                 model_type="chat")
    react = dspy.ReAct(dspy.Signature("question -> answer",
                                      common.SYSTEM),
                       tools=[common.list_files, common.read_file,
                              common.calculate], max_iters=10)
    def answer(question):
        with dspy.context(lm=lm):
            return react(question=question).answer
    return answer
