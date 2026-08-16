# Prompt files

One file per (role, node type). Fourteen files: `{author,judge}_{root,expose,entity,plot,event,scene,trace}.md`.

**They are deliberately not built from one shared preamble.** EXP-001 measured a
4,561-character failure-derived addendum appended to an existing system prompt:
one clause improved its target metric on both items, one showed no effect, and
one coincided with a regression on the only item where improvement was possible.
The hypothesis that survived is that instruction attention is itself a budget, so
each added clause is paid for by the clauses already there. Until EXP-002 settles
it we assume prompt fixes do not compose, and we keep each call's instruction set
as small as the node type allows.

Concretely:

- The cheat sheets are **sliced by tag**, never injected whole. A ROOT author call
  gets `[ALL]` and `[ROOT]` and nothing else.
- Craft, plot-embedding and prose blocks are injected **only where the node type
  uses them** — the plot-embedding rubric goes to ROOT calls only; the prose ban
  list goes only to calls that write prose.
- The model-notes addendum (`narrativeforge.model_notes.addendum_for`) is
  **opt-in per call**, defaulting to off, because EXP-001's one measured
  regression was on the clause we would most want.

## File format

A `---` fenced header of `key: value` lines, then `# SYSTEM` and `# USER`
sections. `{placeholders}` in the USER body are filled by `distill/context.py`.

| header key | meaning |
|---|---|
| `role` | `author` or `judge` |
| `node_type` | `root`, `expose`, `entity`, `plot`, `event`, `scene`, `trace` |
| `cheatsheet_tags` | comma-separated tags sliced out of the role's cheat sheet |
| `rubric` | rubric id loaded from `distill/rubrics/` |
| `inject` | comma-separated: `craft_sheet`, `craft_checks`, `plot_embedding`, `prose`, `model_notes` |
| `schema` | `narrativeforge.schemas` key, or `-` for free text |

## Prefix-cache ordering

Stable content first, varying content last — measured at 48.9x TTFT reduction on
the local Qwen deployment and 2,400x on the GLM one. Every USER body therefore
puts the cheat sheet, craft block, rubric and source script **before** the
node-specific material, and the artifact-under-review and prior critiques
**last**. Do not reorder without re-measuring `cached_tokens`.
