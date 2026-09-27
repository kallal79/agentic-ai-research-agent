# Agentic AI Research Agent

A small but functional autonomous agent that takes a high-level goal from the user,
breaks it down into steps, and uses multiple tools (web search, Wikipedia, calculator,
text summarizer) to accomplish each sub-task. It handles errors along the way and
produces a final structured report.

Built as a take-home assignment for the Agentic AI Engineer Intern position.

## How to run it

### Prerequisites

- Python 3.9+
- pip

### Setup

```bash
# clone the repo
git clone https://github.com/kallal79/agentic-ai-research-agent.git
cd agentic-ai-research-agent

# create a virtual environment
python -m venv venv

# activate it
# on Windows:
venv\Scripts\activate
# on Mac/Linux:
source venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

### Running

```bash
# interactive mode - it will ask you for a goal
python main.py

# pass a goal directly
python main.py "Research the latest trends in artificial intelligence"

# run one of the built-in demo goals
python main.py --demo

# pick a specific demo (0=research, 1=competitive analysis, 2=travel)
python main.py --demo --goal-index 1

# run all three demos back to back
python main.py --all-demos

# verbose mode (debug logs)
python main.py -v "Research quantum computing"
```

### Running tests

```bash
pytest tests/ -v

# with coverage report
pytest tests/ -v --cov=agent --cov=tools --cov=report
```

## What it does

When you give it a goal like *"Research the latest AI developments"*, the agent:

1. **Plans** - Classifies the intent (research, competitive analysis, or travel) and
   generates an ordered list of steps with tool assignments and fallback strategies.
2. **Executes** - Runs each step by calling the appropriate tool, collects data, and
   passes information between steps.
3. **Handles errors** - If a tool fails, it retries, falls back to a different tool,
   or skips the step and moves on.
4. **Reports** - Produces both a Markdown and a JSON report summarizing everything
   that happened.

## Tools

| Tool | What it does |
|------|--------------|
| `web_search` | Searches the web via DuckDuckGo. Has a mock fallback if the library isn't available. |
| `wikipedia` | Fetches article summaries from Wikipedia. Falls back to the REST API or mock data if needed. |
| `calculator` | Evaluates math expressions safely using Python's AST module (no `eval`). |
| `text_summarizer` | Extractive summarization using word-frequency scoring. No ML model needed. |

## Error handling demo

The first web search call deliberately simulates a timeout so you can see the retry
mechanism in action. After the retry, it works normally. This is controlled by a flag
and can be turned off.

## Project structure

```
.
├── main.py                  # entry point (CLI)
├── requirements.txt
├── agent/
│   ├── planner.py           # goal decomposition
│   ├── executor.py          # step execution engine
│   ├── error_handler.py     # retry / fallback / skip logic
│   └── orchestrator.py      # ties everything together
├── tools/
│   ├── base.py              # base class and ToolResult
│   ├── web_search.py        # DuckDuckGo search
│   ├── wikipedia_tool.py    # Wikipedia lookup
│   ├── calculator.py        # safe math eval
│   └── text_summarizer.py   # extractive summarizer
├── report/
│   └── builder.py           # markdown + JSON report generator
├── tests/
│   ├── test_tools.py        # unit tests for tools
│   └── test_agent.py        # integration tests for agent
├── docs/
│   ├── architecture.md      # architecture diagram (ASCII)
│   ├── writeup.md           # design write-up
│   └── sample_runs/         # sample execution transcripts
└── output/                  # generated reports go here
```

## Docs

- [Architecture](docs/architecture.md) - how the components fit together
- [Design write-up](docs/writeup.md) - decisions, limitations, future work
- [Sample runs](docs/sample_runs/) - 3 example transcripts

## License

MIT
