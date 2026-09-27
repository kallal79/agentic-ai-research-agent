# Sample Run 1 - Research Goal

## Command

```
python main.py "Research and summarize the top 3 developments in artificial intelligence from the last week"
```

## What happened

The agent classified this as a "research" goal and created a 5-step plan:

```
Step 1: Search the web for recent AI info        [web_search]    fallback: wikipedia
Step 2: Look up "artificial intelligence" on Wiki [wikipedia]     no fallback
Step 3: Look up "developments" on Wiki            [wikipedia]     no fallback
Step 4: Summarize everything collected             [text_summarizer]
Step 5: Calculate compression ratio                [calculator]
```

### Execution log

- **Step 1** - web_search timed out on first try (this is the deliberate failure).
  Agent retried and got results on the second attempt. Took about 340ms.
- **Step 2** - Wikipedia lookup for "artificial intelligence" succeeded. Got a
  summary of the article with categories.
- **Step 3** - Wikipedia lookup for "developments" succeeded with article info.
- **Step 4** - Summarizer took all the text from steps 1-3 and produced a
  4-sentence summary. Identified key terms.
- **Step 5** - Calculator computed the compression ratio (summary words / original
  words * 100). Result: 18.45%

### Error recovery

One recovery event occurred:
- Step 1: retry after simulated timeout. Second attempt succeeded.

### Final stats

- Total steps: 5
- Succeeded: 5
- Failed: 0
- Retries: 1
- Success rate: 100%

Reports were saved to `output/report_YYYYMMDD_HHMMSS.md` and `.json`.
