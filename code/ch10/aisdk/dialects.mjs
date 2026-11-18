// dialects.mjs -- one generateText call with a tool, sent through three
// providers of the AI SDK to the same llama-server; a fetch wrapper logs
// which endpoint each provider uses.
// Usage: node dialects.mjs BASE_URL      (e.g. http://127.0.0.1:8080/v1)
import { generateText, tool, stepCountIs } from "ai";
import { createOpenAICompatible } from "@ai-sdk/openai-compatible";
import { createOpenAI } from "@ai-sdk/openai";
import { createAnthropic } from "@ai-sdk/anthropic";
import { z } from "zod";

const baseURL = process.argv[2];
const log = [];
const fetch = async (url, init) => {
  const r = await globalThis.fetch(url, init);
  log.push(`${init.method} ${new URL(url).pathname} -> ${r.status}`);
  return r;
};
const weather = tool({
  description: "Current weather in a city",
  inputSchema: z.object({ city: z.string() }),
  execute: async ({ city }) => ({ city, sky: "cloudy", celsius: 4 }),
});
const models = {
  "openai-compatible": createOpenAICompatible(
    { name: "local", baseURL, fetch }).chatModel("q"),
  "openai (Responses)": createOpenAI(
    { baseURL, apiKey: "none", fetch }).responses("q"),
  "anthropic (Messages)": createAnthropic(
    { baseURL, apiKey: "none", fetch })("q"),
};
for (const [name, model] of Object.entries(models)) {
  log.length = 0;
  try {
    const r = await generateText({
      model, tools: { get_weather: weather }, stopWhen: stepCountIs(3),
      temperature: 0, maxOutputTokens: 300,
      prompt: "What is the weather in Oslo? Use the tool. /no_think",
    });
    const calls = r.steps.flatMap(s => s.toolCalls.map(
      c => `${c.toolName}(${JSON.stringify(c.input)})`));
    console.log(`${name}: ${log.join(", ")}`);
    console.log(`  calls ${calls.join(" ")}; answer ${
      JSON.stringify(r.text.trim().slice(0, 70))}`);
  } catch (e) {
    console.log(`${name}: ${log.join(", ")}\n  error ${e.message.slice(0, 150)}`);
  }
}
