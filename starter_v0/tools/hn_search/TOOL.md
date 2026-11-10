---
name: hn_search
track: bonus
kind: live_api
provider: HN Search by Algolia
requires_env: []
inputs: [query, sort, limit]
outputs: [tool, query, sort, items]
side_effect: false
---

Find Hacker News stories about a topic. `sort=relevance` searches by relevance;
`sort=date` searches newest first. Results include discussion links, story URLs,
points and comment counts. No API key is required.
