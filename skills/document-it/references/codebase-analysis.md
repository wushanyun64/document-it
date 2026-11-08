# From codebase to doc plan

## 1. Run the analyzer

```bash
python3 "$SKILL/scripts/analyze_repo.py" <repo> [--json]
```

It reports (stdlib only, no network): languages by file count, packaging metadata, Python
packages and their public symbols, CLI entry points and CLI frameworks used, config files,
examples/tests/docs dirs, CI workflows, existing docs tooling, and the git remote (→
`repo_url` / `site_url`). It's a starting inventory, not the truth — confirm by reading code.

## 2. Read in this order

1. README and any existing docs — the author's own framing and vocabulary.
2. Packaging (`pyproject.toml`, `package.json`, ...) — name, entry points, extras, Python versions.
3. Public entry points: `__init__.py` / `__all__`, CLI command definitions, HTTP routes.
4. `examples/` and tests — tests show real usage and edge cases; examples show the golden path.
5. Core modules behind the public API — to explain concepts and behavior accurately.
6. Git history of key files (`git log --oneline -20 -- <file>`) — reveals design intent and churn.

## 3. Build the inventory

Fill this table (it becomes the Phase 3 doc map):

| Artifact found | Becomes | Notes |
|---|---|---|
| Public modules/classes/functions | **Reference** (generated API pages) | Docstring quality check: missing docstrings → list them for the user |
| CLI commands & options | **Reference** (generated or `--help` capture) + **How-to** per common task | |
| Config files / env vars / settings models | **Reference** (config table) + **How-to** "Configure X" | One row per option: name, type, default, meaning |
| HTTP API / OpenAPI spec | **Reference** (rendered spec) | |
| Installation & smallest working example | **Tutorial**: Getting started | The golden path |
| `examples/*` | Tutorials (if they teach) or how-tos (if they solve a task) | Include via snippets, don't paste |
| Recurring issues / FAQ / error handling | **How-to** guides | |
| Architecture, data flow, plugins, extension points | **Explanation** + Mermaid diagrams | |
| Design decisions, ADRs, "why not X" | **Explanation** | |
| Contributing, dev setup, release process | How-to (contributors section) | Only if contributors are an audience |
| Changelog | Linked from nav | Don't rewrite |

## 4. Find the golden path

The first tutorial is the single most important page. Pick the shortest path from "nothing
installed" to "a meaningful result the reader can see":
- Look at the README quickstart, the simplest example file, and the most basic test.
- It must work on a clean machine with only the stated prerequisites.
- Ends with a visible success (output, file, running server) and "next steps" links.
- If no clean path exists (needs credentials, services), note it — that's an interview question.

## 5. Identify concepts

List the 5–10 nouns a reader must understand (e.g. *Client, Session, Pipeline, Stage, Plugin*).
For each: one-sentence definition, where it lives in code, how it relates to the others. This
feeds the architecture diagram and a glossary-style explanation page, and fixes terminology.

## 6. Note gaps and risks for the user

- Public symbols without docstrings (reference would be empty) — offer to write docstrings.
- Behavior that's ambiguous or looks buggy — ask, don't document guesses.
- Internal-looking code that's exported — ask whether it's public.
- Non-Python repos: no mkdocstrings autogen; plan hand-written or tool-exported reference (see `site-setup.md`).
