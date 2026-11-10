---
name: wiki
track: bonus
kind: live_api
provider: Wikipedia MediaWiki API
requires_env: []
inputs: [query, lang, limit]
outputs: [tool, query, lang, items]
side_effect: false
---

Search Wikipedia for stable background information, definitions and biographies.
Use `lang=vi` for Vietnamese Wikipedia or `lang=en` for English. Results contain
titles, article URLs and short plain-text excerpts. No API key is required.
