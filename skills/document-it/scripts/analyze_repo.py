#!/usr/bin/env python3
"""Inventory a repository for documentation planning (document-it skill).

Static analysis only: no code is imported or executed, no network access.

Usage:
    python3 analyze_repo.py <repo-root> [--json] [--max-symbols N]
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None

SKIP_DIRS = {
    ".git", ".hg", ".venv", "venv", "env", "node_modules", "__pycache__", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".tox", ".nox", "dist", "build", "site", ".idea", ".vscode",
    "target", ".eggs",
}
LANG_BY_EXT = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin",
    ".rb": "Ruby", ".php": "PHP", ".cs": "C#", ".c": "C", ".h": "C", ".cpp": "C++",
    ".hpp": "C++", ".swift": "Swift", ".scala": "Scala", ".sh": "Shell", ".r": "R", ".jl": "Julia",
}
PACKAGING_FILES = [
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "package.json", "Cargo.toml",
    "go.mod", "pom.xml", "build.gradle", "Gemfile", "composer.json",
]
CONFIG_PATTERNS = [
    "*.env.example", ".env.example", "config.*", "settings.*", "*.config.*", "*.ini", "*.cfg",
    "*.yaml", "*.yml", "*.toml",
]
DOC_TOOL_FILES = {
    "zensical.toml": "Zensical", "mkdocs.yml": "MkDocs", "mkdocs.yaml": "MkDocs", "docs/conf.py": "Sphinx",
    "docusaurus.config.js": "Docusaurus", "docusaurus.config.ts": "Docusaurus",
    "book.toml": "mdBook", ".readthedocs.yaml": "Read the Docs", ".readthedocs.yml": "Read the Docs",
}
CLI_FRAMEWORKS = {"argparse": "argparse", "click": "Click", "typer": "Typer", "fire": "Fire", "docopt": "docopt"}
WEB_FRAMEWORKS = {"fastapi": "FastAPI", "flask": "Flask", "django": "Django", "starlette": "Starlette", "aiohttp": "aiohttp"}


def walk_files(root: Path):
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            entries = list(d.iterdir())
        except OSError:
            continue
        for p in entries:
            if p.is_dir():
                if p.name not in SKIP_DIRS and not p.name.endswith(".egg-info"):
                    stack.append(p)
            elif p.is_file():
                yield p


def rel(p: Path, root: Path) -> str:
    return p.relative_to(root).as_posix()


def git_info(root: Path) -> dict:
    def run(*args):
        try:
            out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=10)
            return out.stdout.strip() if out.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None

    remote = run("remote", "get-url", "origin")
    info = {"is_repo": run("rev-parse", "--is-inside-work-tree") == "true", "remote": remote}
    info["default_branch"] = (run("symbolic-ref", "--short", "refs/remotes/origin/HEAD") or "").removeprefix("origin/") or run("branch", "--show-current")
    m = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote or "")
    if m:
        owner, repo = m.groups()
        info["repo_url"] = f"https://github.com/{owner}/{repo}"
        info["repo_name"] = f"{owner}/{repo}"
        info["site_url_guess"] = f"https://{owner.lower()}.github.io/{repo}/"
    return info


def read_pyproject(root: Path) -> dict:
    path = root / "pyproject.toml"
    if not path.exists() or tomllib is None:
        return {}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError):
        return {"error": "could not parse pyproject.toml"}
    project = data.get("project", {})
    poetry = data.get("tool", {}).get("poetry", {})
    return {
        "name": project.get("name") or poetry.get("name"),
        "description": project.get("description") or poetry.get("description"),
        "requires_python": project.get("requires-python"),
        "scripts": project.get("scripts") or poetry.get("scripts") or {},
        "urls": project.get("urls", {}),
        "optional_dependencies": sorted((project.get("optional-dependencies") or {}).keys()),
        "build_backend": data.get("build-system", {}).get("build-backend"),
    }


def read_package_json(root: Path) -> dict:
    path = root / "package.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"error": "could not parse package.json"}
    bin_ = data.get("bin")
    if isinstance(bin_, str):
        bin_ = {data.get("name", "bin"): bin_}
    return {
        "name": data.get("name"), "description": data.get("description"),
        "bin": bin_ or {}, "main": data.get("main"), "types": data.get("types"),
        "scripts": sorted((data.get("scripts") or {}).keys()),
    }


def find_python_packages(root: Path) -> tuple[Path, list[Path]]:
    src = root / "src"
    base = src if src.is_dir() and any((d / "__init__.py").exists() for d in src.iterdir() if d.is_dir()) else root
    pkgs = [
        d for d in sorted(base.iterdir())
        if d.is_dir() and (d / "__init__.py").exists() and d.name not in SKIP_DIRS
        and d.name not in {"tests", "test", "docs", "tools", "examples", "scripts", "benchmarks"}
    ]
    return base, pkgs


def public_symbols(path: Path) -> dict:
    """Top-level public classes/functions, __all__, docstring presence, frameworks imported."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return {"error": "unparseable"}
    explicit_all = None
    classes, functions, undocumented, imports = [], [], [], set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            try:
                explicit_all = list(ast.literal_eval(node.value))
            except (ValueError, SyntaxError):
                pass
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
            (classes if isinstance(node, ast.ClassDef) else functions).append(node.name)
            if ast.get_docstring(node) is None:
                undocumented.append(node.name)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imports.add(node.module.split(".")[0])
    return {
        "module_docstring": ast.get_docstring(tree) is not None,
        "all": explicit_all, "classes": classes, "functions": functions,
        "undocumented": undocumented, "imports": sorted(imports),
    }


def analyze(root: Path, max_symbols: int) -> dict:
    files = list(walk_files(root))
    rels = [rel(f, root) for f in files]
    langs = Counter(LANG_BY_EXT[f.suffix.lower()] for f in files if f.suffix.lower() in LANG_BY_EXT)

    report: dict = {
        "root": str(root),
        "git": git_info(root),
        "languages": dict(langs.most_common()),
        "packaging_files": [p for p in PACKAGING_FILES if (root / p).exists()],
        "pyproject": read_pyproject(root),
        "package_json": read_package_json(root),
        "readme": next((r for r in rels if re.fullmatch(r"README(\.\w+)?", r, re.I)), None),
        "community_files": [r for r in rels if "/" not in r and re.match(r"(LICENSE|CONTRIBUTING|CHANGELOG|CODE_OF_CONDUCT|SECURITY)", r, re.I)],
        "docs_tooling": sorted({tool for f, tool in DOC_TOOL_FILES.items() if (root / f).exists()}),
        "docs_files": sorted(r for r in rels if r.startswith("docs/") and r.endswith((".md", ".rst", ".ipynb")))[:200],
        "examples": sorted(r for r in rels if re.match(r"(examples?|samples?|demos?)/", r))[:100],
        "tests_dirs": sorted({r.split("/")[0] for r in rels if re.match(r"tests?/", r)}),
        "ci_workflows": sorted(r for r in rels if r.startswith(".github/workflows/")),
        "config_files": sorted(r for r in rels if "/" not in r and any(Path(r).match(p) for p in CONFIG_PATTERNS) and r not in PACKAGING_FILES)[:50],
        "openapi_specs": sorted(r for r in rels if re.search(r"(openapi|swagger)\.(json|ya?ml)$", r, re.I)),
    }

    if langs.get("Python"):
        base, pkgs = find_python_packages(root)
        py = {"source_root": rel(base, root) if base != root else ".", "packages": [], "cli_frameworks": [], "web_frameworks": []}
        all_imports: set[str] = set()
        missing_docstrings = []
        for pkg in pkgs:
            modules = []
            for f in sorted(pkg.rglob("*.py")):
                if any(part in SKIP_DIRS for part in f.parts):
                    continue
                mod = ".".join(f.relative_to(base).with_suffix("").parts).removesuffix(".__init__")
                info = public_symbols(f)
                all_imports.update(info.get("imports", []))
                private = any(part.startswith("_") and part != "__init__" and part != "__main__" for part in f.relative_to(base).with_suffix("").parts)
                missing_docstrings += [f"{mod}.{s}" for s in info.get("undocumented", [])] if not private else []
                modules.append({
                    "module": mod, "private": private,
                    "classes": info.get("classes", [])[:max_symbols], "functions": info.get("functions", [])[:max_symbols],
                    "all": info.get("all"), "has_docstring": info.get("module_docstring", False),
                })
            py["packages"].append({"name": pkg.name, "path": rel(pkg, root), "modules": modules})
        py["cli_frameworks"] = sorted(v for k, v in CLI_FRAMEWORKS.items() if k in all_imports)
        py["web_frameworks"] = sorted(v for k, v in WEB_FRAMEWORKS.items() if k in all_imports)
        py["main_modules"] = sorted(r for r in rels if r.endswith("__main__.py"))
        py["public_symbols_missing_docstrings"] = missing_docstrings[:100]
        py["missing_docstrings_count"] = len(missing_docstrings)
        report["python"] = py

    report["suggested_quadrants"] = suggest(report)
    return report


def suggest(r: dict) -> list[str]:
    s = []
    py = r.get("python", {})
    name = r["pyproject"].get("name") or r["package_json"].get("name") or Path(r["root"]).name
    s.append(f"Tutorial: 'Getting started with {name}' — golden path from install to first result"
             + (f" (base it on {r['examples'][0]})" if r["examples"] else " (no examples/ dir — derive from README/tests)"))
    if r["pyproject"].get("scripts") or r["package_json"].get("bin") or py.get("cli_frameworks"):
        s.append("Reference: CLI page (--help captured at build time via markdown-exec); How-to: one per common command workflow")
    if py.get("packages"):
        s.append(f"Reference: generated API pages for {', '.join(p['name'] for p in py['packages'])} (api-autonav + mkdocstrings)")
        if py.get("missing_docstrings_count"):
            s.append(f"Gap: {py['missing_docstrings_count']} public symbols lack docstrings — offer to write them")
    if r["config_files"] or r["pyproject"].get("optional_dependencies"):
        s.append("Reference: configuration/options table; How-to: 'Configure …' guides")
    if r["openapi_specs"] or py.get("web_frameworks"):
        s.append("Reference: HTTP API (render OpenAPI spec)")
    s.append("Explanation: architecture overview with Mermaid component diagram + generated import graph")
    if r["docs_tooling"] or r["docs_files"]:
        s.append(f"Existing docs found ({', '.join(r['docs_tooling']) or 'plain files'}) — ask: keep, migrate, or replace")
    if "Python" not in r["languages"] and r["languages"]:
        s.append(f"Primary language {next(iter(r['languages']))}: no mkdocstrings autogen — plan tool-exported or hand-written reference")
    return s


def to_markdown(r: dict) -> str:
    out = [f"# Repository inventory: `{r['root']}`", ""]
    g = r["git"]
    out += ["## Repo", f"- git: {'yes' if g.get('is_repo') else 'no'}; remote: {g.get('remote') or '—'}; default branch: {g.get('default_branch') or '—'}"]
    if g.get("repo_url"):
        out.append(f"- repo_url: {g['repo_url']} · site_url (Pages guess): {g['site_url_guess']}")
    out += ["", "## Languages (files)", ", ".join(f"{k} {v}" for k, v in r["languages"].items()) or "—", ""]
    out += ["## Packaging & metadata", f"- files: {', '.join(r['packaging_files']) or '—'}"]
    for key in ("pyproject", "package_json"):
        meta = {k: v for k, v in r[key].items() if v}
        if meta:
            out.append(f"- {key}: " + "; ".join(f"{k}={v}" for k, v in meta.items()))
    out += ["", "## Existing docs & community files",
            f"- README: {r['readme'] or 'missing'}",
            f"- community files: {', '.join(r['community_files']) or '—'}",
            f"- docs tooling: {', '.join(r['docs_tooling']) or 'none'}; docs files: {len(r['docs_files'])}",
            f"- examples: {len(r['examples'])} files{(' (e.g. ' + ', '.join(r['examples'][:5]) + ')') if r['examples'] else ''}",
            f"- tests dirs: {', '.join(r['tests_dirs']) or '—'}; CI workflows: {', '.join(r['ci_workflows']) or '—'}",
            f"- top-level config files: {', '.join(r['config_files']) or '—'}",
            f"- OpenAPI specs: {', '.join(r['openapi_specs']) or '—'}", ""]
    py = r.get("python")
    if py:
        out += ["## Python", f"- source root: `{py['source_root']}`; CLI frameworks: {', '.join(py['cli_frameworks']) or '—'}; web: {', '.join(py['web_frameworks']) or '—'}"]
        if py["main_modules"]:
            out.append(f"- __main__ modules: {', '.join(py['main_modules'])}")
        for pkg in py["packages"]:
            out.append(f"\n### Package `{pkg['name']}` ({pkg['path']})")
            out.append("| module | public classes | public functions | `__all__` | docstring |")
            out.append("|---|---|---|---|---|")
            for m in pkg["modules"]:
                if m["private"]:
                    continue
                out.append(f"| `{m['module']}` | {', '.join(m['classes']) or '—'} | {', '.join(m['functions']) or '—'} | "
                           f"{'yes' if m['all'] is not None else '—'} | {'yes' if m['has_docstring'] else '**no**'} |")
            priv = [m["module"] for m in pkg["modules"] if m["private"]]
            if priv:
                out.append(f"\nPrivate modules (excluded by default): {', '.join(priv)}")
        if py["missing_docstrings_count"]:
            out.append(f"\n**{py['missing_docstrings_count']} public symbols without docstrings**, e.g.: {', '.join(py['public_symbols_missing_docstrings'][:15])}")
        out.append("")
    out += ["## Suggested doc map seeds", *[f"- {s}" for s in r["suggested_quadrants"]], ""]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    ap.add_argument("--max-symbols", type=int, default=25, help="max symbols listed per module")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    report = analyze(root, args.max_symbols)
    print(json.dumps(report, indent=2) if args.json else to_markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
