# gsm.py -- an Inspect task: the first 100 GSM8K test questions, scored
# on the last number of the reply.
import re
from inspect_ai import Task, task
from inspect_ai.dataset import Sample, hf_dataset
from inspect_ai.scorer import (CORRECT, INCORRECT, Score, Target,
                               accuracy, scorer, stderr)
from inspect_ai.solver import TaskState, generate, prompt_template

PROMPT = ("{prompt}\n\nSolve the problem step by step. End with a last "
          "line of the form '#### <number>'.")

def record(r):
    return Sample(input=r["question"],
                  target=r["answer"].split("#### ")[-1].replace(",", ""))

def last_number(text):
    found = re.findall(r"-?\d[\d,]*(?:\.\d+)?", text)
    return found[-1].replace(",", "") if found else None

@scorer(metrics=[accuracy(), stderr()])
def last_number_match():
    async def score(state: TaskState, target: Target):
        answer = last_number(state.output.completion)
        ok = answer is not None and float(answer) == float(target.text)
        return Score(value=CORRECT if ok else INCORRECT, answer=answer)
    return score

@task
def gsm100():
    return Task(
        dataset=hf_dataset("openai/gsm8k", name="main", split="test",
                           sample_fields=record, limit=100),
        solver=[prompt_template(PROMPT), generate()],
        scorer=last_number_match())
