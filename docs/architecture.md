# Architecture

## Overview

The system follows a simple pipeline: the user provides a goal, the planner breaks
it into steps, the executor runs each step using tools, and a report is generated
at the end.

```
User Goal (CLI)
     |
     v
+-------------------+
|    Orchestrator    |   <-- coordinates the whole process
+-------------------+
     |
     v
+-------------------+
|     Planner       |   <-- figures out what steps are needed
+-------------------+
     |
     v
+-------------------+       +----------------+
|    Executor       |------>| Web Search     |  (DuckDuckGo)
|                   |------>| Wikipedia      |  (API)
|                   |------>| Calculator     |  (AST-based)
|                   |------>| Summarizer     |  (frequency scoring)
+-------------------+
     |
     |  on failure:
     v
+-------------------+
|  Error Handler    |   retry -> fallback -> skip
+-------------------+
     |
     v
+-------------------+
|  Report Builder   |   --> Markdown + JSON files
+-------------------+
```

## How the planner works

The planner looks at the goal text and classifies it into one of three categories
based on keyword matching:

- **Research** - default; generates steps like "search the web for X", "look up X
  on Wikipedia", "summarize everything", "calculate compression ratio"
- **Competitive analysis** - triggered by words like "competitor", "company",
  "market"; adds extra search steps for competitor data
- **Travel** - triggered by "travel", "itinerary", "trip"; includes a budget
  calculation step

Each step specifies which tool to use and optionally a fallback tool.

## How the executor works

It walks through the steps in order. For each step it:

1. Prepares the input arguments (sometimes injecting data from previous steps)
2. Calls the tool's `safe_execute()` method
3. If it succeeds, stores the result and moves on
4. If it fails, asks the ErrorHandler what to do:
   - **retry**: try the same tool again (up to 2 retries)
   - **fallback**: try the fallback tool instead
   - **skip**: mark the step as failed and continue

## Data flow between steps

The executor keeps a running buffer of text from all steps. When the summarizer
runs, it gets the accumulated text as input. When the calculator runs, it gets
dynamically generated expressions based on previous results (like word count
ratios).

## Tool interface

Every tool extends `BaseTool` and returns a `ToolResult` object with:
- `status` (success/failure/timeout/partial)
- `data` (the actual payload)
- `error_msg` (what went wrong, if anything)
- `duration_ms` (how long it took)

This way the executor doesn't need to know anything about the tool internals.
It just checks `result.ok` and handles the outcome.
