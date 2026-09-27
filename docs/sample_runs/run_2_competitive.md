# Sample Run 2 - Competitive Analysis

## Command

```
python main.py "Given a company name Tesla, produce a short competitive-landscape brief using public web data"
```

## What happened

The planner picked up keywords like "company", "competitive", "landscape" and
classified this as a competitive analysis goal. It generated a 5-step plan:

```
Step 1: Search web for Tesla's competitive landscape  [web_search]    fallback: wikipedia
Step 2: Get Tesla background from Wikipedia            [wikipedia]
Step 3: Search web for Tesla's competitors             [web_search]    fallback: wikipedia
Step 4: Summarize all competitive intelligence         [text_summarizer]
Step 5: Calculate metrics                              [calculator]
```

### Execution log

- **Step 1** - First attempt timed out (deliberate), retried and got 5 results.
- **Step 2** - Wikipedia returned Tesla's article summary and categories.
- **Step 3** - Second web search for competitors worked on first try (the
  deliberate failure only triggers once).
- **Step 4** - Summarizer compiled everything into a 5-sentence overview.
- **Step 5** - Calculator computed the compression ratio: 22.31%

### Observations

The planner made two separate web searches - one for general competitive landscape
and one specifically for competitors. This is a nice example of domain-appropriate
decomposition without any LLM involved, just templates triggered by intent
classification.

### Final stats

- Total steps: 5
- Succeeded: 5
- Failed: 0
- Retries: 1
- Success rate: 100%
