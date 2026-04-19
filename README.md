# TopicVisExplorer (next branch - v1.0 in development)

This is the **modernization branch** of TopicVisExplorer. The paper-era code
lives on the `master` and `legacy` branches, and at the immutable
[`v0.1-paper`](https://github.com/gonzalezf/TopicVisExplorer/releases/tag/v0.1-paper)
git tag.

This branch is an **orphan branch** (no shared history with `master`). It
holds the rewrite as a clean, pip-installable Python library backed by a
FastAPI server and a Vite-built TypeScript bundle of the existing D3
visualisations. When v1.0 ships it will be promoted to the default branch.

## Status

Bootstrap in progress. Phase 1 (`pyproject.toml`, src layout, ported algorithm
core, unit + golden tests) will land here next.

For the paper version of the code, install it from the legacy branch:

```bash
git clone https://github.com/gonzalezf/TopicVisExplorer.git
cd TopicVisExplorer
git checkout legacy
# then follow legacy/README.md
```

## Citation

If you use this software, please cite the Journal of Visualization paper
(see `CITATION.cff`, added in Phase 5).
