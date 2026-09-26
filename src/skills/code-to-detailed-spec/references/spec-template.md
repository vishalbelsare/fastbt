# Detailed Spec Template

# <Name> Spec

<spec_meta>
Name:
Target platform:
Source scope:
Output mode:
</spec_meta>

<purpose>
## Purpose

Describe the business or system behavior this spec defines.
</purpose>

<scope>
## Scope

State what is included and excluded.
</scope>

<inputs>
## Required Inputs

- Input:
- Type:
- Required:
- Default:
- Validation:
</inputs>

<validation>
## Validation

- Reject the configuration when:
- Normalize inputs by:
</validation>

<state_model>
## State Model

- State:
- Transition:
- Stored fields:
</state_model>

<workflow>
## Workflow

1. First decision or action.
2. Next decision or action.
</workflow>

<decision_ordering>
## Decision Ordering

1. Highest-priority decision.
2. Next decision.
3. Final fallback.
</decision_ordering>

<failure_handling>
## Failure Handling

- Missing data:
- Stale data:
- Rejections:
- Partial completion:
- Timeout:
</failure_handling>

<portability_notes>
## Portability Notes

- Platform-specific assumptions that must be preserved:
- Vendor- or tool-specific details intentionally excluded:
</portability_notes>

<invariants>
## Invariants

- This must always be true.
</invariants>

<audit_events>
## Required Operational Events

- Event:
- Required fields:
- When emitted:
</audit_events>
