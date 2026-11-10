---
name: github_repos
track: bonus
kind: live_api
provider: GitHub REST API
requires_env: []
inputs: [query, language, sort, limit]
outputs: [tool, query, language, sort, items]
side_effect: false
---

Search public GitHub repositories by topic, with an optional programming
language filter. Sort by best match, stars or latest update. Results contain
repository links, descriptions, language and star counts. Unauthenticated API
access is rate limited; errors are returned as data rather than raised.
