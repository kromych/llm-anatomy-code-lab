"""The DSPy port without model_type="chat": which dialect does DSPy speak
by default? Put the first question to it through the logging proxy and
read the paths and the status codes in the proxy's log.

Usage: python3 dspy_default.py BASE_URL   (for example
       http://127.0.0.1:8182/dspy-default/v1)
"""
import sys
import dspy
import common

lm = dspy.LM("openai/local", api_base=sys.argv[1], api_key="none",
             temperature=0, max_tokens=1024, cache=False)
react = dspy.ReAct(dspy.Signature("question -> answer", common.SYSTEM),
                   tools=[common.list_files, common.read_file,
                          common.calculate], max_iters=10)
with dspy.context(lm=lm):
    try:
        print("ANSWER", react(question=common.TASKS[0][1]).answer)
    except Exception as e:
        print("ERROR", repr(e)[:800])
