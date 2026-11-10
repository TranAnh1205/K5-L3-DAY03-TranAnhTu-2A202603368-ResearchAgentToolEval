---
name: calculator
track: bonus
kind: local_formatter
requires_env: []
inputs: [expression]
outputs: [expression, result]
side_effect: false
---
# calculator

Safely evaluate mathematical expressions and calculations for research data.
`expression` is a mathematical expression string (e.g. '125 * 34', 'sqrt(144) + 10').
