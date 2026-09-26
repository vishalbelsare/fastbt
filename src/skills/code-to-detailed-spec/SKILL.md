---
name: code-to-detailed-spec
description: Convert code, tests, or partial docs into detailed, implementation-free specifications. Use when the user needs a structured spec for handoff, migration, rewrite, live-system conversion, cross-platform implementation, or machine-readable requirements, especially when output must exclude code, tests, or run results.
---

# Code To Detailed Spec

Convert implementation behavior into a clear, standalone specification a developer, analyst, or downstream system can implement elsewhere.

The goal is not to explain the code. The goal is to extract the contract hidden inside the code and write it as requirements.

Treat this skill as model- and platform-agnostic:

- do not assume a specific LLM, agent framework, runtime, or prompt surface
- use neutral terms such as requester, source implementation, and downstream implementer
- prefer requirements that remain valid across languages, stacks, and execution environments

## Core Workflow

1. Inventory the implementation surface:
   - source files
   - public entry points
   - helper modules
   - config schemas
   - tests or examples that clarify behavior
   - existing specs or docs
2. Trace actual behavior:
   - inputs and defaults
   - validation
   - state and lifecycle
   - selection or routing logic
   - main workflows
   - ordering of decisions
   - retries, cooldowns, and limits
   - error, missing-data, and edge-case behavior
   - emitted events, logs, outputs, or persistence side effects
3. Build a discrepancy report before writing or updating the final spec.
4. Halt if there are unresolved discrepancies, ambiguous rules, or logical contradictions.
5. Proceed to the spec only after the discrepancies are resolved by code evidence, existing requirements, or explicit user direction.
6. Separate implementation mechanics from portable contract:
   - keep behavior that another platform must reproduce
   - omit language, framework, test, kernel, storage, or backtest-only details unless they are part of the required contract
7. Write the spec in standalone terms. A developer should not need to read the original code to understand the required behavior.
8. Validate the output against the user's exclusion rules, such as no code, no tests, no results, or no implementation notes.

## Discrepancy Gate

The spec must be unambiguous and logically consistent.

Before writing the final spec, check for:

- code paths that contradict each other
- implementation behavior that contradicts an existing spec
- tests that imply behavior not present in code
- parameters whose meaning changes between entry, exit, retry, or reporting
- defaults that are defined in more than one place
- impossible state transitions
- exit or retry rules whose ordering changes outcomes
- missing behavior for invalid inputs, missing data, partial execution, timeouts, or failures
- domain rules that are unsafe for the target platform
- requirements that cannot be inferred from the available evidence

If any item is unresolved, stop and return a discrepancy report instead of writing the final spec.

The discrepancy report must include:

- severity
- affected behavior
- evidence from code, docs, or tests
- why the rule is ambiguous or contradictory
- the minimum decision needed to continue

Do not guess through material ambiguity. A guessed spec is worse than no spec.

If you need a starting template for the final spec, use `references/spec-template.md`.

## Output Modes

Default to human-readable Markdown.

Use XML tags only when the requester asks for machine parsing, structured handoff between tools or systems, or stable section extraction. XML tags help parsers identify sections and fields, but they add visual noise for humans.

Do not use XML tags as a substitute for clear prose. Use them as stable boundaries around clear prose.

If XML-tagged output is required, read `references/xml-tagged-mode.md` before writing the spec.

## Recommended Markdown Sections

Use only the sections that fit the domain:

- Purpose
- Scope
- Required Inputs
- Configuration
- Validation
- State Model
- Data Model
- Selection Rules
- Workflow
- Entry Rules
- Exit Rules
- Decision Ordering
- Retry And Re-entry Rules
- Error Handling
- Missing Data And Staleness
- Execution Confirmation
- Concurrency And Async Requirements
- Security And Permissions
- Invariants
- Observability And Audit Events
- Acceptance Criteria

## Strict Exclusion Rules

When the user asks for specs only:

- Do not include code snippets.
- Do not include test cases.
- Do not include command output.
- Do not include PnL, benchmark, or run results.
- Do not include source-file lists unless the user asks for audit traceability.
- Do not include "source of truth" sections that point back to code.
- Do not include implementation recommendations unrelated to required behavior.

## Portability Rules

When writing the final spec:

- describe behavior in product or system terms, not in terms of one model vendor or orchestration framework
- avoid assuming prompt syntax, role names, tool APIs, or memory systems unless they are part of the required contract
- replace agent-specific wording with neutral counterparts unless the requester explicitly wants agent-oriented language
- if structured output is required, describe the structure itself rather than assuming a specific parser or platform
- include implementation-specific details only when another implementation must preserve them for correctness

## Live Trading Profile

If the source implementation is a trading system or the user asks to convert backtest code into live trading behavior, read `references/live-trading-profile.md` and apply its requirements before writing the spec.

## Final Validation Checklist

Before finishing:

- Confirm the spec can be read without the original code.
- Confirm all required behavior is stated as requirements, not commentary.
- Confirm every material rule has evidence or explicit user direction.
- Confirm decision ordering is explicit where ordering changes outcomes.
- Confirm missing-data and failure behavior is explicit.
- Confirm there are no unresolved contradictions.
- Confirm output obeys the user's requested format and exclusions.

## Gotchas

- **Do not write the final spec if discrepancies are unresolved.** Return a discrepancy report instead.
- **"No code" means no inline snippets, not just no full files.** This includes pseudocode that mirrors the original implementation.
- **Live trading conversion requires explicit fill/confirmation behavior.** Orders do not change state until fills are confirmed.
- **Defaults defined in multiple places are a discrepancy.** The spec must resolve them, not silently pick one.
- **Tests that assert behavior not visible in code are evidence, not proof.** Treat them as a discrepancy to investigate.
- **Platform-agnostic language is required unless the user explicitly asks otherwise.** Avoid naming specific languages, frameworks, or agent tools in the final spec.
