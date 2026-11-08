# Diagrams

These diagrams are **generated from the source code on every docs build**, so they always
reflect the current structure. For the intended design and the reasoning behind it, see
[Explanation](../explanation/index.md).

<!-- Runs at build time via markdown-exec; configure with DOCS_* env vars (see tools/docs/gen_diagrams.py). -->
```python exec="on"
import sys; sys.path.insert(0, "tools/docs")
import gen_diagrams; print(gen_diagrams.render_from_env())
```
