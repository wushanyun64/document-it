# Publishing to GitHub Pages

## Option A — Unversioned with Zensical (default)

Template: `templates/workflows/docs-deploy.yml` → `.github/workflows/docs-deploy.yml`.

On every push to the default branch (and manual dispatch) it: checks out, installs Graphviz
and the docs requirements, runs `zensical build --clean --strict`, uploads `site/` as a Pages
artifact, and deploys with `actions/deploy-pages`. No `gh-pages` branch involved.

One-time manual setup (tell the user):
1. Repo **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. Push to the default branch; the site appears at `https://<owner>.github.io/<repo>/`.
3. Make sure `site_url` in `zensical.toml` is that URL (canonical links, sitemap, 404 page).
4. Until that first deploy, the site URL returns 404. If the README or docs link to it, the
   first PR's `docs-check` link check fails; add `--exclude '^<site_url>'` to the lychee `args`
   in `docs-check.yml`, or deploy once from the default branch before opening PRs.

## Option B — Versioned docs (fallback stack)

Use only when users run several released versions and need a version switcher. `mike` (the
versioning tool) supports MkDocs/ProperDocs but **not Zensical yet**, so this option uses
`templates/mkdocs-legacy/`:

| From | To |
|---|---|
| `templates/mkdocs-legacy/mkdocs.yml` | `mkdocs.yml` (instead of `zensical.toml`) |
| `templates/mkdocs-legacy/requirements-docs.txt` | `requirements-docs.txt` |
| `templates/mkdocs-legacy/docs-deploy-versioned.yml` | `.github/workflows/docs-deploy.yml` |

`docs/`, `tools/docs/`, and the other workflows are the same; in `docs-check.yml` and
`docs-ai-update.yml` replace `zensical build --clean --strict` with `properdocs build --strict`.

Behavior:
- Push to default branch → deploys version `dev`.
- Push tag `vX.Y.Z` → deploys version `X.Y` with alias `latest`, and sets `latest` as default.
- `mike` commits built sites to the `gh-pages` branch, so the Pages source must be
  **Deploy from a branch → `gh-pages` / root** (not "GitHub Actions").
- Prune old versions occasionally: `mike delete --push 0.9`.

Tell the user the trade-off: this stack is on Material for MkDocs, which is in maintenance
mode (critical fixes only). Zensical reads `MIKE_DOCS_VERSION` already, so once mike or
Zensical ships native versioning, migrate back to Option A plus that.

## Custom domain

1. Create `docs/CNAME` containing just the domain (e.g. `docs.example.com`) — it's copied into the site root.
2. DNS: `CNAME docs.example.com → <owner>.github.io` (apex domains: A/ALIAS records to GitHub's Pages IPs).
3. Settings → Pages → Custom domain → enter it → **Enforce HTTPS** once the cert is issued.
4. Set `site_url = "https://docs.example.com/"`.

## Discoverability

- Repo **About** sidebar → Website: the docs URL (user does this; or `gh repo edit --homepage <url>`).
- README: docs badge + link near the top:
  `[![Docs](https://img.shields.io/badge/docs-online-blue)](https://<owner>.github.io/<repo>/)`
- Python: `pyproject.toml` → `[project.urls] Documentation = "<url>"` (shows on PyPI).
- Search is built in; `site_url` enables `sitemap.xml`.

## Private repositories

- GitHub Pages from private repos needs GitHub Pro/Team/Enterprise; the site is still
  **public** unless the org is on Enterprise Cloud with Pages access control.
- If docs must stay private and that's not available: build in CI and upload `site/` as a
  workflow artifact, or host behind auth elsewhere (e.g. Cloudflare Pages + Access). Ask the user.

## Pre-publish checklist

- [ ] `zensical build --clean --strict` reports "No issues found" locally
- [ ] `site_url`, `repo_url`, `edit_uri` correct
- [ ] No secrets, internal hostnames, or customer data in docs or examples
- [ ] Pages source set correctly for the chosen option
- [ ] First deploy run green; open the URL and click through each nav section and a generated API page
