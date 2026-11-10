---
name: confirm_action
track: core
kind: control
requires_env: []
inputs: [action, details]
outputs: [tool, action, details, awaiting_user]
side_effect: false
---
# confirm_action

Ask the user to confirm a potentially irreversible action
before executing it.