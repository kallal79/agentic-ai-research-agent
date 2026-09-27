# Sample Run 3 - Travel Planning

## Command

```
python main.py "Plan a 3-day itinerary for Tokyo, respecting a budget of $500 and interests in food and culture"
```

## What happened

Keywords like "travel", "itinerary", "trip", "budget" triggered the travel planning
template. The planner generated:

```
Step 1: Search for Tokyo attractions and tips    [web_search]    fallback: wikipedia
Step 2: Get Tokyo background from Wikipedia      [wikipedia]
Step 3: Search for Tokyo budget travel info      [web_search]    fallback: wikipedia
Step 4: Estimate trip cost (3 * $150/day)        [calculator]
Step 5: Summarize into itinerary overview        [text_summarizer]
```

### Execution log

- **Step 1** - Simulated timeout on first try, retried and got 5 results about
  Tokyo attractions, food spots, and cultural sites.
- **Step 2** - Wikipedia returned Tokyo's article with city overview and categories.
- **Step 3** - Budget travel search returned 3 results about cost estimates.
- **Step 4** - Calculator computed 3 * 150 = $450 estimated total cost. (The
  $150/day is a default estimate since we can't reliably extract numbers from
  search snippets without NLU.)
- **Step 5** - Summarizer pulled together all the travel info into a 5-sentence
  overview with key terms like "tokyo", "food", "culture".

### Observations

This is the plan type that benefits most from the calculator tool - it does an
actual budget computation. The travel template also shows how the planner adapts
its step sequence based on goal classification. The budget calculation is a bit
simplistic (hard-coded daily rate) but it demonstrates the principle.

### Final stats

- Total steps: 5
- Succeeded: 5
- Failed: 0
- Retries: 1
- Success rate: 100%
