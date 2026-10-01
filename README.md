# Agentic AI Research Agent 2.0 (Autonomous Intelligence System)

A production-grade, fault-tolerant autonomous agent built with **Self-Reflection & Critique**, **Autonomous Dynamic Replanning**, **Sandboxed Code Execution**, and **Multi-Tool Research Pipelines**. It decomposes complex natural language goals, coordinates multi-step investigations, self-heals upstream failures, and produces comprehensive analytical intelligence reports.

Built as an advanced submission for the **Agentic AI Engineer Intern** position.

---

## Key Features & New Capabilities

| Capability | Description |
|------------|-------------|
| **Multi-Tool Research Pipeline** | Seamlessly orchestrates 6 specialized tools across academic, web, encyclopedia, computation, and synthesis domains. |
| **Self-Reflection & Critique Engine** | Evaluates gathered intelligence against high-level goals on Execution Health, Information Density, and Keyword Coverage (0–100 score). |
| **Autonomous Dynamic Replanning** | When self-reflection detects knowledge gaps (completeness < 75%), the agent dynamically injects targeted supplementary research steps. |
| **ArXiv Academic Research Tool** | Queries the public arXiv API for peer-reviewed papers, extracting titles, authors, published dates, abstracts, and direct URLs. |
| **Sandboxed Python Code Executor** | Executes mathematical algorithms and data analytics in an isolated Python environment protected by an AST security validator. |
| **Multi-Turn Session Memory** | Preserves context, entities, and summaries across multiple turns, enabling iterative conversational exploration. |
| **3-Tier Fault Tolerance** | Automated Exponential Retries &rarr; Semantic Fallback Alternatives &rarr; Graceful Degradation with telemetry logging. |
| **Interactive Glassmorphic Web UI** | Real-time web dashboard (running at `http://localhost:5050`) with live telemetry, dynamic step timeline, architecture view, and raw JSON export. |
| **Automated Benchmark Suite** | Multi-domain evaluation suite (`evaluate_agent.py`) assessing agent performance across 5 diverse tasks with 100% task completion. |

---

## Available Tools

| Tool | Trigger / Intent | What it does |
|------|------------------|--------------|
| `arxiv_search` | Academic / Papers | Queries arXiv REST API for peer-reviewed papers, authors, and abstracts. |
| `code_executor` | Data / Python Code | Executes Python numerical algorithms in a sandboxed AST-verified environment. |
| `web_search` | Web Information | Searches current live web via DuckDuckGo with rate-limit and network resilience. |
| `wikipedia` | Foundational Knowledge | Fetches encyclopedic summaries from Wikipedia REST API with fallback caching. |
| `calculator` | Mathematical Expressions | Evaluates arithmetic expressions safely using Python's AST parser. |
| `text_summarizer` | Synthesis & Condensation | Extractive frequency-based summarizer distilling large corpus into key points. |

---

## Quick Start

### 1. Prerequisites & Virtual Environment

```bash
# Clone the repository
git clone https://github.com/kallal79/agentic-ai-research-agent.git
cd agentic-ai-research-agent

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate       # On Windows
# source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Interactive Web Dashboard

Launch the local web server:

```bash
python web_ui.py
```

Open your browser to: **`http://localhost:5050`**

- **Live Agent Console**: Input any natural-language goal or click one-click presets.
- **Decomposed Flow**: Watch real-time execution, retry triggers, and dynamic replanning.
- **Self-Reflection Score**: Inspect completeness metrics, confidence ratings, and critique.
- **System Architecture**: View interactive SVG diagrams of the 3-Tier agent lifecycle.
- **Evaluation Dashboard**: Review telemetry metrics across 40 evaluation traces.

### 3. Run via Command Line (CLI)

```bash
# Interactive mode (prompts for goal)
python main.py

# Direct goal execution
python main.py "Find latest arXiv papers on quantum computing error correction algorithms"

# Sandboxed Python code analysis
python main.py "Execute python code script to compute statistical benchmarks on dataset"

# Run built-in demo presets (0=research, 1=competitive, 2=travel)
python main.py --demo --goal-index 0

# Run all 3 baseline demos sequentially
python main.py --all-demos
```

### 4. Run Automated Benchmark Evaluation Suite

```bash
python evaluate_agent.py
```

Runs 5 standardized benchmarks across Academic, Data Analysis, Competitive Intelligence, General Research, and Logistics. Outputs summary metrics and saves `benchmark_results.json`.

### 5. Run Random Data Generator & Fuzzing Suite

```bash
python generate_random_data.py
```

Generates 38+ synthetic random test traces with precision/recall labels across 6 domains (Academic, Code, Competitive, Research, Travel, and Adversarial/Edge Cases). Exports to `submission_files/synthetic_random_traces.json` and `.csv`, and executes live verification on random inputs.

### 6. Running Tests

```bash
# Run all 58 unit, integration, and random data fuzzing tests (100% pass)
pytest tests/ -v

# Run with test coverage
pytest tests/ -v --cov=agent --cov=tools --cov=report
```

---

## Benchmark Evaluation Results

| Benchmark Task | Domain | Execution Time | Steps Completed | Reflection Score | Status |
|----------------|--------|----------------|-----------------|------------------|--------|
| **BM-01** | Academic / Scientific (arXiv) | 4.0s | 3 / 4 | 80.0% (HIGH) | **PASS** |
| **BM-02** | Empirical Data Computation (Python) | 1.3s | 4 / 4 | 52.5% (LOW) | **PASS** |
| **BM-03** | Competitive Intelligence (NVIDIA) | 6.4s | 5 / 6 | 37.0% (LOW) | **PASS** |
| **BM-04** | General Topic Research (Solar) | 4.8s | 4 / 5 | 35.0% (LOW) | **PASS** |
| **BM-05** | Travel & Budget Planning (Tokyo) | 4.2s | 5 / 6 | 37.0% (LOW) | **PASS** |

- **Tasks Passed**: **5 / 5 (100%)**
- **Overall Step Success Rate**: **84.0%**
- **Total Test Suite**: **58 / 58 Passed (100%)**
- **Session Memory Turns Retained**: **5**
- **Random Data Verification**: **100% Zero-Crash Resilience on Adversarial & Edge Cases**

---

## Project Structure

```
.
├── main.py                  # CLI entry point with demo modes
├── web_ui.py                # Next-Gen Web UI & API server (port 5050)
├── evaluate_agent.py        # Automated 5-domain benchmark evaluation suite
├── generate_random_data.py  # Random test trace generator & live fuzzer
├── benchmark_results.json   # Machine-readable evaluation metrics
├── requirements.txt         # Project dependencies
├── agent/
│   ├── planner.py           # Goal decomposition & intent classification
│   ├── executor.py          # Step execution & dynamic data piping
│   ├── error_handler.py     # 3-tier recovery (retry, fallback, skip)
│   ├── reflection.py        # Self-Reflection, gap detection & replanning
│   ├── memory.py            # Multi-turn session context & entity linking
│   └── orchestrator.py      # High-level coordinator tying all modules
├── tools/
│   ├── base.py              # BaseTool interface & ToolResult dataclass
│   ├── arxiv_tool.py        # ArXiv academic paper retrieval tool
│   ├── code_executor.py     # AST-sandboxed Python code execution tool
│   ├── web_search.py        # DuckDuckGo search tool
│   ├── wikipedia_tool.py    # Wikipedia article extraction tool
│   ├── calculator.py        # AST arithmetic calculation tool
│   └── text_summarizer.py   # Frequency-based extractive text summarizer
├── report/
│   └── builder.py           # Markdown & JSON report compilation engine
├── tests/
│   ├── test_random_data.py  # Fuzz tests, empty inputs, keyboard mash, edge cases
│   ├── test_new_features.py # Tests for arXiv, code executor, reflection, memory
│   ├── test_tools.py        # Unit tests for baseline tools
│   └── test_agent.py        # Integration tests for agent lifecycle
└── docs/
    ├── architecture.md      # Architecture documentation
    ├── writeup.md           # Engineering writeup & design trade-offs
    └── sample_runs/         # Sample execution transcripts
```

---

## License

MIT License &copy; Kallal Mukherjee
