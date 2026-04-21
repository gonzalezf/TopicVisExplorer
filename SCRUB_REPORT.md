# Privacy / security scrub report

**Date:** 2026-04-20  
**Target branch:** `next` (private backup)  
**Purpose:** audit the tree for privacy/security risks before extracting
v1.0.0 to the public `TopicVisExplorer` repository (GitHub: `gonzalezf/TopicVisExplorer`; previously published under `topicvisexplorer-lib` before rename).

This file is **not copied** to the public repo. It stays in the private
backup as an audit record.

---

## Summary

Four findings, all resolved. No secrets, no credentials, no private datasets
will ship in the extracted v1.0.0 tarball.

| # | Category | Finding | Action |
|---|----------|---------|--------|
| 1 | Personal email | `felipe.gonzalez@dal.ca` hardcoded in dead `user_study_code.js` | Deleted the two `user_study_code.js` copies and the matching `user_study_code.html` template; removed stale references in `main.ts`, `vite.config.ts`, `globals.d.ts`, and `frontend/README.md`. |
| 2 | Paper manuscript | `paper_in_review/Journal_of_visualization.zip` + `.pdf` | Kept in the private backup; **excluded from the extraction rsync**. |
| 3 | Private dataset references | `CONTRIBUTING.md` + `golden_baseline/README.md` + `frontend/tests/visual.spec.ts` mentioned specific private corpora ("Cambridge Analytica", "airlines", "europe_dataset"). | Rewrote all three to point at synthetic fixtures + `PAPER_REPRO.md`. No dataset names remain in the tree. |
| 4 | Internal planning notes | `PLAN.md` (modernization plan with local paths like `/root/projects/...` and `agent@topicvisexplorer.local` identity marker) | Kept in the private backup; **excluded from the extraction rsync**. |

---

## Scans performed

### IP addresses

```text
Pattern:  \b(?:\d{1,3}\.){3}\d{1,3}\b
          (plus narrower: (10|172|192|169|100|198|203)\.\d+\.\d+\.\d+)
Hits:     127.0.0.1 (intentional, documented loopback), SVG path coords,
          "5.15.1" Font Awesome version strings.
Verdict:  no real network addresses.
```

### Email addresses

```text
Pattern:  [\w._+-]+@[\w.-]+\.[a-z]{2,}
Hits:     felipe.gonzalez@dal.ca   — real personal email → removed (finding #1)
          felipe.gonzalez@example.com — placeholder in pyproject.toml, safe
          agent@topicvisexplorer.local — PLAN.md only, excluded from extract
          jb@eaio.com, i@izs.me, wenzhixin2010@gmail.com — third-party OSS
            library author attribution, left intact
Verdict:  no private emails in the extracted tree.
```

### Local filesystem paths

```text
Pattern:  /(home|Users|mnt/data|root/projects|root/[A-Za-z])
Hits:     PLAN.md only.
Verdict:  PLAN.md excluded from extraction.
```

### Hostnames / cloud metadata

```text
Pattern:  topicviz | localhost:[0-9]{4,5} | 169.254.169.254 | amazonaws
          | gcp | azure
Hits:     localhost:5173, localhost:8000 (dev-server docs), nothing else.
Verdict:  no cloud/metadata leakage.
```

### Secret markers

```text
Pattern:  api[_-]?key | secret[_-]?key | password\s*= | token\s*= |
          BEGIN (RSA|OPENSSH) PRIVATE
Hits:     `idx2token` (adapter field name, not a secret),
          FontAwesome `kitToken` read from a config global (not hardcoded),
          minified Bootstrap JS string matches.
Verdict:  no hardcoded secrets.
```

### Large / binary blobs

```text
Command:  find . -size +500k ...
Hits:     paper_in_review/*.pdf and .zip (2 MB each) → excluded from extract
          frontend/node_modules/... → excluded from extract (not in git)
          golden_baseline/tiny_prepare_output.json (700 KB) → synthetic,
            safe to ship
Verdict:  no unexpected binary payloads in the extracted tree.
```

### Pickles / key-vectors / model artifacts

```text
Command:  find . -name '*.pkl' -o -name '*.kv' -o -name '*.model'
Hits:     none.
Verdict:  no model artifacts in the tree.
```

---

## Extraction exclude list (final)

The rsync in the next step will exclude:

```
.git/
.venv*/
node_modules/
.mypy_cache/
.pytest_cache/
.ruff_cache/
.benchmarks/
site/                                    # mkdocs build output
dist/                                    # python build output
frontend/dist/                           # vite dev-mode output
src/topicvisexplorer/web/dist/           # vite-built bundle (rebuilt in new repo)
frontend/test-results/
frontend/playwright-report/
__pycache__/
*.pyc
.coverage
.coverage.*
paper_in_review/                         # finding #2
PLAN.md                                  # finding #4
SCRUB_REPORT.md                          # this file
.github/workflows/legacy-smoke.yml       # references legacy/ branch
```

After rsync the scrub scans are re-run on the new tree (§ "post-extract
validation" in the plan).
