---
name: confirm_action
track: core
kind: control
requires_env: []
inputs: [action, details, question]
outputs: [tool, action, details, question, awaiting_user]
side_effect: false
---
# confirm_action

Ask the user to confirm a potentially irreversible action
before executing it.
