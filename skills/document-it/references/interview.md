# Interviewing the user

Goal: settle every decision that changes the output, with as few questions as possible.
Run Phase 1 (discovery) first — anything the repo can answer, you answer yourself.

## Rules

1. **Infer, don't ask.** Never ask what the code tells you: language, package name, repo URL,
   CLI names, whether `examples/` exists, current docs tool, CI provider, license.
   State your inferences instead: "I see a Typer CLI `foo` and a Python API `foo.client` — I'll
   document both as public."
2. **Batch.** At most 4 questions per round, 1–3 rounds total. Most important first.
3. **Offer defaults.** Every question gets a recommended option (listed first, marked
   "Recommended") so the user can accept quickly. With `AskUserQuestion`, use 2–4 options;
   the tool adds "Other" automatically.
4. **Ask about ambiguities with evidence.** Quote the file/symbol: "`src/foo/_compat.py` and
   `src/foo/legacy/` look internal — exclude from reference?"
5. **Stop when it stops mattering.** If a remaining unknown wouldn't change the doc map, pick the
   default and mention it in the Phase 3 proposal.
6. **Re-runs:** if `docs/.doc-spec.yml` exists, read it and only ask about what's new.

## Question bank

### Round 1 — Readers and scope (always ask)

| Question | Options (recommended first) | Why it matters |
|---|---|---|
| Who are the main readers? | Developers using the library/CLI · Contributors to the project · Both (separate sections) · Non-technical end users | Sets tone, assumed knowledge, and whether a Contributing/Internals section exists |
| What should a reader be able to do after the docs? | (free-form or 2–3 inferred goals from the README/examples) | Picks the tutorial's golden path and top how-tos |
| Which parts are in scope? | Public API + CLI (exclude `_private` and internal modules) · Everything · Specific packages | Controls reference generation filters |
| Which doc types, in what priority? | All four; tutorial + reference first · Reference + how-to only · Start with a getting-started tutorial | Sizes the work |

### Round 2 — Publishing and maintenance

| Question | Options | Why it matters |
|---|---|---|
| Publish to GitHub Pages? | Yes, via GitHub Actions · No, docs in repo only | Whether deploy workflow is added |
| Versioned docs? | No, always latest (simplest; Zensical) · Yes, a version per release tag (fallback stack: ProperDocs + mike, since mike doesn't support Zensical yet) | Picks site generator and deploy template |
| Custom domain? | No (`<user>.github.io/<repo>`) · Yes: ___ | CNAME + `site_url` |
| How should docs keep up with code? | CI regenerates reference + checks drift, and Claude proposes doc PRs on source changes · CI regeneration + drift check only (no API key) · Manual only | Which workflows are added; AI needs `ANTHROPIC_API_KEY` and reads contributor-written code (prompt-injection surface, contained by the template; see `auto-update.md`). Recommend CI-only for repos that merge outside PRs without close review |

Note when relevant: Pages on **private** repos requires a paid GitHub plan; the published
site is public unless on Enterprise Cloud with access control.

### Round 3 — Only if needed

- Existing docs found: keep as-is and add around them · migrate into the new structure · replace.
- Tone: friendly/conversational · neutral/formal. Brand colors or logo?
- Docs language(s) other than English?
- Specific unclear behavior found in code (quote it) — what is the intended behavior?
- Anything readers frequently get wrong / support questions that recur? (great how-to sources)

## Recording answers — `docs/.doc-spec.yml`

Write this after the interview (template in `templates/docs/.doc-spec.yml`). It is read by
re-runs of this skill and by the AI update workflow, so keep it accurate and concise.

```yaml
project: mypkg
audiences:
  - name: library users
    level: intermediate Python developers
    goals: [install and make a first request, configure auth, handle errors]
scope:
  include: [src/mypkg]
  exclude: [src/mypkg/_internal, src/mypkg/legacy]
quadrants: [tutorials, how-to, reference, explanation]
tone: friendly, second person, concise
publishing: {github_pages: true, versioned: false, custom_domain: null}
auto_update: {ci_regenerate: true, drift_check: true, ai_pr: true}
conventions:
  runnable_python_fence: python
  illustrative_fence: py
  terminology: {client: "Client (never 'connector')"}
decisions:
  - "Two CLIs exist; only `mypkg` is public, `mypkg-dev` is excluded."
```
