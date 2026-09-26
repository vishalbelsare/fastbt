```markdown
# Spec Title

<spec_meta>
Name: Example Workflow
Source scope: implementation behavior only
Target platform: live service
</spec_meta>

<purpose>
## Purpose

Plain-language purpose.
</purpose>

<inputs>
## Required Inputs

- Input name: requirement and constraints.
</inputs>

<workflow>
## Workflow

1. First required step.
2. Second required step.
</workflow>

<invariants>
## Invariants

- Condition that must always hold.
</invariants>
```

XML tag rules:

- Use lowercase snake_case tag names.
- Keep tags shallow: one tag per major section.
- Do not deeply nest tags unless the user explicitly needs a strict schema.
- Keep every opening tag paired with a closing tag.
- Do not wrap every bullet or sentence.
- Prefer stable section tags over generated ids.
- Include a `<discrepancy_gate>` section only when unresolved issues exist.
