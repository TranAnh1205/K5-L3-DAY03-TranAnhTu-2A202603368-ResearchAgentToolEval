---
name: normalize_handle
track: bonus
kind: local_formatter
requires_env: []
inputs: [screenname]
outputs: [tool, screenname]
side_effect: false
---
# normalize_handle

Normalize a social media username by removing @ and whitespace. The
registered `timeline` tool calls this helper internally before the API request.
