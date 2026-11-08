# Writing each Diátaxis quadrant

Page templates live in `$SKILL/templates/pages/`. Copy one, fill it in, delete unused sections.

## Tutorials — learning-oriented

**Purpose:** give a newcomer a successful first experience and confidence. You are responsible
for their success: every step must work exactly as written.

Must have:
- What they'll build/achieve (one sentence + ideally a screenshot or output sample)
- Prerequisites (versions, accounts) and time estimate
- Numbered steps, each with a concrete action and the **expected result** shown
- A finish line ("You now have…") and "Next steps" links to how-tos/explanation

Do: one linear path, no choices ("we'll use SQLite"), small visible wins every few steps,
repeat the full command each time.
Don't: explain theory (link to explanation instead), offer alternatives, cover edge cases,
assume prior knowledge of the project.

## How-to guides — task-oriented

**Purpose:** help a competent user accomplish one specific real-world goal.

Must have:
- Title as the goal: "How to rotate API keys", "Deploy behind a reverse proxy"
- One-line "when you need this" and prerequisites
- Numbered steps; branches only where reality branches ("If you use Docker, …")
- Verification step ("Confirm it worked by…")
- Related links (reference for options, explanation for background)

Do: assume competence, focus on the goal not the tool, keep it short.
Don't: teach basics, explain why at length, document every option (link to reference).

## Reference — information-oriented

**Purpose:** accurate, complete, consistently structured description to look things up.

- **Generate it** wherever possible (mkdocstrings, CLI help, OpenAPI, config schema).
- Hand-written reference (config tables, error codes, file formats) follows a fixed structure:
  name · type · default · description · example. Same order everywhere.
- Mirror the code's structure (one page per module / command / resource).
- Do: be austere, complete, and neutral. Include short usage examples.
- Don't: give instructions or opinions or explanation beyond a sentence.

Docstring style for generated reference (pick the project's existing style; default Google):

```py
def fetch(url: str, *, timeout: float = 10.0) -> Response:
    """Fetch a URL and return the response.

    Args:
        url: Absolute URL to fetch.
        timeout: Seconds before giving up.

    Returns:
        The parsed response.

    Raises:
        TimeoutError: If the server doesn't answer within ``timeout``.

    Example:
        >>> fetch("https://example.com").status
        200
    """
```

## Explanation — understanding-oriented

**Purpose:** deepen understanding — context, design, trade-offs, alternatives, history.

Must have:
- A clear topic in the title: "About the plugin system", "Why we use event sourcing"
- Diagram(s) where structure or flow matters (architecture overview is the anchor page)
- Connections: how this concept relates to others, links to reference/how-to

Do: discuss, give reasons, admit trade-offs, use analogies.
Don't: include step-by-step instructions or exhaustive option lists.

## Landing pages

- `docs/index.md`: what the project is (2 sentences), who it's for, a minimal example, and a
  4-card grid linking the quadrants (template provided).
- Each quadrant's `index.md`: one paragraph on what's in this section + list of pages with one-line descriptions.

## Style guide

- **Second person, active voice, present tense.** "Run `foo init`." not "The init command should be run."
- **Short sentences and paragraphs.** One idea per paragraph; ≤ ~25 words per sentence.
- **Front-load.** Put the key point or action first in each section and sentence.
- **Exact names in code font:** `ClassName`, `--flag`, `config.yaml`, `ENV_VAR`.
- **Every command block shows what to expect** (output block or a sentence).
- **Consistent terminology** — one word per concept (record it in `.doc-spec.yml`).
- **Admonitions sparingly:** `!!! note`, `!!! warning` for things that bite, `!!! tip` for shortcuts. Max ~1 per screen.
- **Headings are descriptive**, sentence case, no "Introduction"/"Overview" filler where avoidable.
- **Code:** runnable Python fenced ```` ```python ```` (CI-tested); fragments ```` ```py ````; shells ```` ```bash ```` without `$` prompts so copy works; use code annotations/tabs (Material) for alternatives like pip/uv.
- **Links:** relative Markdown links between pages (`../reference/config.md`) so `--strict` catches breaks.
- **Accessibility:** alt text on images, captions on diagrams, don't rely on color alone.

## Quality checklist (per page)

- [ ] Exactly one quadrant; title reflects it
- [ ] Reader and goal are obvious in the first 2 lines
- [ ] Every code sample verified against current code (ideally included from a real file)
- [ ] Expected output shown after commands
- [ ] Links to the neighbouring quadrants
- [ ] No orphan page — it's in `nav`
- [ ] Diagram (if any) has caption and alt text, ≤ ~15 nodes
