# Design Write-Up

## Design decisions

**Rule-based planner instead of using an LLM**

I went with a keyword-based intent classifier and template-driven plan generator
rather than calling an LLM API. The main reason is that this makes the project
completely self-contained - no API keys needed, and anyone can run it immediately.
The architecture itself doesn't change if you swap in an LLM-backed planner later;
the Executor and tools work the same way regardless.

**Uniform tool interface**

All tools inherit from `BaseTool` and return `ToolResult` objects. The executor
doesn't need any tool-specific logic - it just calls `safe_execute()` and checks
the result. Adding a new tool means implementing three things: `name`, `description`,
and `execute()`. That's it.

**Deliberate failure simulation**

The web search tool deliberately fails on its first call with a simulated timeout.
This way reviewers can see the full error recovery path without needing to unplug
their internet. It's toggled via a flag, so it can be turned off for normal use.

**Three-tier error recovery**

When a tool fails, the ErrorHandler decides what to do next:
1. Retry the same tool (up to 2 times)
2. Fall back to a different tool if one is specified
3. Skip the step and continue with the rest of the plan

Every recovery action gets logged so it shows up in the final report.

**Data piping between steps**

The executor keeps a text buffer that accumulates output from each step. The
summarizer gets this buffer as input, and the calculator gets dynamically computed
expressions based on the summarizer's output. This shows inter-step data flow
without coupling the tools to each other.

## Limitations

- The planner uses keyword matching, not actual NLU. Unusual or ambiguous goals
  will probably get suboptimal plans.
- The summarizer is purely extractive (word frequency scoring). It works okay for
  factual snippets but not so well for conversational or narrative text.
- Steps run sequentially. In a real system you'd want to parallelize independent
  steps.
- No memory across runs. Each invocation starts from scratch.

## What I'd do with more time

- Hook up an actual LLM for planning (probably via LangChain or direct API calls)
  so the agent can handle arbitrary goals instead of relying on templates.
- Add async execution for independent steps using `asyncio`.
- Build a tool discovery system where the planner picks tools based on their
  descriptions rather than hard-coded mappings.
- Create an evaluation harness that tests the agent against a suite of goals
  and scores plan quality, tool accuracy, and recovery effectiveness.
- Add a simple web frontend (Flask or FastAPI) for non-CLI users.
- Cache API responses to avoid hitting rate limits during development.
