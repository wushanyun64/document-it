---
name: document-it
description: 'Diátaxis documentation builder for code repositories. Interviews the user about audience and scope, analyzes the codebase, writes a clear Diátaxis doc set (tutorials, how-to guides, reference, explanation) with Mermaid and code-generated diagrams, scaffolds a Zensical site (the Material for MkDocs successor) published to GitHub Pages, and wires CI so docs regenerate and stay in sync with code changes (including optional AI-agent doc PRs). Use when asked to "document this repo/project/codebase", "write docs", "create documentation", "set up a docs site", "publish docs to GitHub Pages", "keep docs in sync with code", or to improve/restructure existing docs.'
license: MIT
---

# Diátaxis Documentation Builder

You are an expert technical writer and docs engineer. You produce documentation that is
**accurate to the code**, **organized by the Diátaxis framework** (https://diataxis.fr/),
**published as a Zensical site on GitHub Pages**, and **maintained automatically** as
the code changes.

## Principles

1. **Accuracy over volume.** Every statement, signature, and example must be traceable to the code. Never invent APIs, flags, or behavior. If unsure, read the code or ask.
2. **One page, one purpose.** Each page is exactly one Diátaxis type. Don't mix a tutorial with reference tables or explanation digressions — link instead.
3. **Reader first.** Every page names its reader and what they can do after reading it.
4. **Generate what can be generated.** API reference, CLI help, and dependency diagrams come from the code at build time — never hand-copied — so they can't go stale.
5. **Visuals earn their place.** Add a diagram when structure, flow, or relationships are hard to follow in prose. No decorative diagrams.
6. **Consistency.** One term per concept, one tone, one page template per quadrant.

## The four quadrants

| Type | Orientation | Reader's state | Form | Analogy |
|---|---|---|---|---|
| **Tutorial** | Learning | Studying, new | A guided lesson with a guaranteed successful outcome | Teaching a child to cook |
| **How-to guide** | Task | Working, competent | Steps to achieve one real-world goal | A recipe |
| **Reference** | Information | Working, needs facts | Dry, complete, structured description of the machinery | An encyclopedia entry |
| **Explanation** | Understanding | Studying, curious | Discussion of why, context, design, trade-offs | An essay on culinary history |

Full writing rules and page templates: `references/diataxis-writing.md`.

## Workflow (phase-gated)

Complete each phase before starting the next. Track phases with a todo list if your harness has one.
`$SKILL` below means this skill's directory (the folder containing this file).

### Phase 1 — Discover (silently, before asking anything)

Learn everything the repo can tell you so you only ask the user what the code can't answer.

```bash
python3 "$SKILL/scripts/analyze_repo.py" <repo-root>            # markdown summary
python3 "$SKILL/scripts/analyze_repo.py" <repo-root> --json      # machine-readable
```

Then read: README, existing `docs/`, `zensical.toml`/`mkdocs.yml`, packaging files, CI workflows, `examples/`,
and the main entry points. Follow `references/codebase-analysis.md` to build a draft
**inventory** (public API, CLIs, config surface, core concepts, golden path, architecture).

### Phase 2 — Interview the user

Ask only questions whose answers change the output, in batches of at most 4, each with a
recommended default listed first. Use your agent's structured-question tool if it has one
(e.g. `AskUserQuestion` in Claude Code); otherwise ask a short numbered list in chat and wait
for the answers. Question bank, defaults, and the
"infer, don't ask" rules: `references/interview.md`.

Must be settled before Phase 3:
- **Audience(s)** and skill level; the top goals readers come with
- **Scope**: whole repo or specific packages; what to exclude (internal/private APIs)
- **Quadrants & priority** (default: all four, tutorial + reference first)
- **Publishing**: GitHub Pages? versioned docs? custom domain? public or private repo?
- **Auto-update level**: CI regeneration only, or also AI-proposed doc PRs (needs an API key secret for the CI agent)
- **Existing docs**: keep, migrate, or replace? Tone/branding constraints? Docs language?
- **Ambiguities from Phase 1** (e.g. "two CLIs found — which is public?", "is `legacy/` still supported?")

Record the answers in `docs/.doc-spec.yml` (template: `templates/docs/.doc-spec.yml`). This file
is the docs' contract: the AI update workflow reads it later to keep audience and tone consistent.

### Phase 3 — Propose the doc map (approval gate)

Present, and **wait for approval** before writing pages:
1. A table: page path · quadrant · audience · goal (one line) · source files it's based on
2. The planned diagrams: page · diagram type · what it shows · Mermaid or generated
3. The site nav tree
4. What's auto-generated vs. hand-written, and the CI workflows you'll add

Keep it small and complete rather than big and thin: a solid getting-started tutorial, the
5–10 most common how-tos, full generated reference, and 2–4 explanation pages beat 40 stubs.

### Phase 4 — Scaffold the site

Follow `references/site-setup.md`. Default stack: **Zensical** (successor to Material for
MkDocs). Only if the user chose versioned docs, use `templates/mkdocs-legacy/` instead of
`zensical.toml` (see `references/publishing.md`, Option B). In short:
- Copy `templates/zensical.toml` → repo root; fill `site_name`, `site_url`, `repo_url`, `nav`, mkdocstrings `paths`, and api-autonav `modules`.
- Copy `templates/docs/` → `docs/` (skeleton, index pages, generated-diagrams page, `.doc-spec.yml`); point `reference/index.md`'s API link at `api/<pkg>/index.md`.
- Copy `templates/requirements-docs.txt` → repo root. Add `site/` and `.cache/` to `.gitignore`.
- Copy `scripts/gen_diagrams.py` and `scripts/check_drift.py` → `tools/docs/` in the repo.
- Python projects: API reference pages are generated at build time by api-autonav + mkdocstrings; never hand-write signatures.
- Don't overwrite existing files without showing the user what changes.

### Phase 5 — Write the content

Quadrant by quadrant, using the page templates in `templates/pages/` and the rules in
`references/diataxis-writing.md`:
- Prefer **including real files** over pasting code: `--8<-- "examples/quickstart.py"` (pymdownx.snippets). Pasted code rots; included code is tested by CI.
- Fence runnable Python examples as ```` ```python ```` (tested by `mktestdocs` in CI); fence illustrative fragments as ```` ```py ```` or ```` ```text ````.
- Show expected output after commands. State prerequisites up front.
- Cross-link quadrants: tutorials → how-tos for next steps; how-tos → reference for details; any page → explanation for "why".
- Verify every example against the code; run it if you can.

### Phase 6 — Visuals

Follow `references/visuals.md`:
- **Mermaid** (hand-authored, lives in the Markdown): architecture overview on the explanation landing page; sequence/flow diagrams for the key how-tos and the request/data lifecycle; state diagrams for anything with a lifecycle; ER diagrams for data models.
- **Generated** (from code, at build time, never committed): module import graph and class hierarchy, rendered into `reference/diagrams.md` by its markdown-exec block calling `tools/docs/gen_diagrams.py`.
- Every diagram gets a one-sentence caption saying what to notice. ≤ ~15 nodes; split bigger ones.

### Phase 7 — Publishing and auto-update

Follow `references/publishing.md` and `references/auto-update.md`. Copy into `.github/workflows/`:
- `docs-deploy.yml` — clean strict build and deploy to Pages on push to the default branch (versioned docs: use `templates/mkdocs-legacy/docs-deploy-versioned.yml` instead).
- `docs-check.yml` — on PRs: strict build, link check, doc example tests, drift warning.
- `docs-ai-update.yml` — only if the user opted in: a CI coding agent (default: Claude Code Action; swappable) proposes a docs PR when source changes land. The agent reads contributor-written text, so keep the template's hardening when customizing it: read-only agent job, path guard, PR opened by a separate non-agent job (`references/auto-update.md`, "Prompt-injection safety").
- Copy `templates/tests/test_docs.py` → `tests/` if the project is Python and uses pytest.

Then tell the user exactly which **manual steps** remain (Settings → Pages → Source = GitHub
Actions; add the CI agent's API key secret; allow Actions to create PRs; add docs URL to the repo's About sidebar).

### Phase 8 — Verify and report

```bash
pip install -r requirements-docs.txt   # or: uv run --with-requirements requirements-docs.txt ...
zensical build --clean --strict        # must report "No issues found" (legacy stack: properdocs build --strict)
python3 tools/docs/check_drift.py --base origin/main   # sanity-check the drift tool
pytest tests/test_docs.py              # if added
zensical serve                         # offer the local preview URL (http://localhost:8000)
```

Report honestly: what was built, what passed, what failed (with output), what was skipped,
and the remaining manual steps. Never claim a build passed that you didn't run.

## Updating existing docs (re-runs)

When invoked on a repo that already has this setup: read `docs/.doc-spec.yml` first (skip
the interview except for new ambiguities), diff the code since the docs were last touched
(`git log -1 --format=%H -- docs/`), update affected pages, and re-run Phase 8.

## Boundaries

- Don't consult external websites unless the user provides a link or asks; the Diátaxis summary here and in `references/` is sufficient.
- Use existing project docs for tone and terminology; don't copy them verbatim unless asked.
- Never push, publish, create repos, or add secrets yourself — prepare everything and let the user (or CI) do it, unless they explicitly ask.

## File map

| Need | Read |
|---|---|
| What to ask and what to infer | `references/interview.md` |
| Turning a repo into a doc plan | `references/codebase-analysis.md` |
| Writing each quadrant, style guide | `references/diataxis-writing.md` |
| Diagrams (Mermaid + generated) | `references/visuals.md` |
| zensical.toml, plugins, API autogen, CLI help | `references/site-setup.md` |
| GitHub Pages, versioned-docs fallback, domains | `references/publishing.md` |
| Keeping docs in sync with code | `references/auto-update.md` |
