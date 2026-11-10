---
name: dedupe_sources
track: bonus
kind: local_formatter
requires_env: []
inputs: [items]
outputs: [items, unique_count, duplicate_count]
side_effect: false
---
# dedupe_sources

Removes repeated research sources from a list of items. It keeps the first item
for each URL, ignoring URL fragments and common tracking parameters such as
`utm_source`. Items without a URL remain separate. This tool does not search or
fetch sources and makes no network request.
