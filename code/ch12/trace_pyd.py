"""Run one PydanticAI task with OpenTelemetry spans kept in memory; print
the answer, each span with its attributes as a line of JSON, and a table of
the spans. Usage: python3 trace_pyd.py BASE_URL QUESTION"""
import json, sys
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic_ai import Agent
from pydantic_ai.models.instrumented import InstrumentationSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
import common

exp = InMemorySpanExporter()
tp = TracerProvider(); tp.add_span_processor(SimpleSpanProcessor(exp))
model = OpenAIChatModel("local", provider=OpenAIProvider(base_url=sys.argv[1], api_key="none"))
agent = Agent(model, instructions=common.SYSTEM,
              tools=[common.list_files, common.read_file, common.calculate])
agent.instrument = InstrumentationSettings(tracer_provider=tp, include_content=False)
print("ANSWER", agent.run_sync(sys.argv[2]).output)
spans = exp.get_finished_spans()
byid = {s.context.span_id: s for s in spans}
def depth(s):
    d = 0
    while s.parent is not None and s.parent.span_id in byid:
        s = byid[s.parent.span_id]; d += 1
    return d
for s in sorted(spans, key=lambda s: s.start_time):
    a = dict(s.attributes)
    print(json.dumps({"depth": depth(s), "name": s.name,
        "ms": round((s.end_time - s.start_time) / 1e6),
        "attrs": {k: v for k, v in a.items() if k.startswith("gen_ai") or k in ("agent_name", "server.address", "server.port")}}))

def first(a, *names):
    return next((a[n] for n in names if n in a), "")
print("%-26s%4s%8s%8s%8s  %s" % ("span", "ms", "input", "cached", "output",
                                 "finish"))
for s in sorted(spans, key=lambda s: s.start_time):
    a = dict(s.attributes)
    u = "gen_ai.usage." if "gen_ai.usage.input_tokens" in a \
        else "gen_ai.aggregated_usage."
    print(("%-26s%4d%8s%8s%8s  %s" % (
        "  " * depth(s) + s.name, round((s.end_time - s.start_time) / 1e6),
        first(a, u + "input_tokens"), first(a, u + "cache_read.input_tokens"),
        first(a, u + "output_tokens"),
        " ".join(a.get("gen_ai.response.finish_reasons", ())))).rstrip())
