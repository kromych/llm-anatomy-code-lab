# agent_eval.py -- the eight workspace tasks of Chapter 11 as an Inspect
# task. The solver runs our own agent (code/ch11/agent.py) as a black box,
# and the scorer applies the whole-word rule of Chapter 11.
import asyncio, json, pathlib, re, sys, urllib.request
from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import ModelOutput
from inspect_ai.scorer import (CORRECT, INCORRECT, Score, Target,
                               accuracy, scorer, stderr)
from inspect_ai.solver import TaskState, solver

CH11 = pathlib.Path(__file__).resolve().parent.parent / "ch11"
sys.path.insert(0, str(CH11))
import agent, evaluate, tools
tools.ROOT = CH11 / "ws"
SYSTEM = agent.SYSTEM
HINT = (" The workspace holds configuration files, data and logs; when "
        "a question names no file, search for one.")
LOCK = asyncio.Lock()          # agent.chat is global: one sample at a time

def make_chat(temperature, seed):
    def chat(messages, base, timeout=300):
        body = {"model": agent.MODEL, "messages": messages,
                "temperature": temperature, "seed": seed,
                "tools": [s for _, s in tools.TOOLS.values()],
                "chat_template_kwargs": {"enable_thinking": False}}
        req = urllib.request.Request(
            base + "/chat/completions", json.dumps(body).encode(),
            {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    return chat

@solver
def our_agent(base, temperature, hint):
    async def solve(state: TaskState, generate):
        async with LOCK:
            agent.chat = make_chat(temperature, seed=state.epoch)
            agent.SYSTEM = SYSTEM.replace(" Answer", HINT + " Answer"
                                          ) if hint else SYSTEM
            answer, messages = await asyncio.to_thread(
                agent.run, state.input_text, base)
        state.output = ModelOutput.from_content("our-agent", answer or "")
        state.metadata["turns"] = sum(m["role"] == "assistant"
                                      for m in messages)
        return state
    return solve

@scorer(metrics=[accuracy(), stderr()])
def whole_word():
    async def score(state: TaskState, target: Target):
        text = state.output.completion.replace(",", "")
        ok = re.search(rf"(?<![\w.]){re.escape(target.text)}(?!\w|\.\d)", text)
        return Score(value=CORRECT if ok else INCORRECT,
                     answer=state.output.completion)
    return score

@task
def workspace(base="http://127.0.0.1:8086/v1", temperature=0.0,
              hint=False):
    return Task(dataset=[Sample(input=q, target=a)
                         for q, a in evaluate.TASKS],
                solver=our_agent(base, float(temperature), bool(hint)),
                scorer=whole_word())
