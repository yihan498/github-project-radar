---
name: github-project-radar
description: Discover, rank, locally archive, and deeply analyze noteworthy GitHub open-source projects. Use for daily or scheduled GitHub recommendations, fast-rising/new/classic repository discovery, README-and-source-backed project research, local cold storage, and long-form Chinese project analysis explaining what a repository does and what can be learned from it.
---

# GitHub Project Radar

Run a source-first daily research workflow. Produce one strong recommendation rather than many shallow summaries.

## Workflow

1. Use `assets/config.json` as defaults unless the user supplies overrides.
2. Run `python scripts/radar.py discover --workspace <workspace>`. Set `GITHUB_TOKEN` when available; unauthenticated API use has stricter limits.
3. Read `<workspace>/data/candidates/YYYY-MM-DD.json`. Check diversity across `new`, `active`, `classic`, and verified `rising` signals. Treat its `discovery_score` only as a metadata pre-screen, never as the final recommendation score.
4. Read `references/evaluation-rubric.md` completely. Shortlist 3–5 candidates across at least two signal classes, archive the strongest 2–3, and create one scorecard per archived candidate from `assets/evaluation-template.json`.
5. Run `python scripts/radar.py validate-scorecard --file <scorecard>` for every scorecard. Apply all hard gates before comparing totals. Select the highest passing candidate; if scores are within 3 points, prefer higher evidence sufficiency, then higher personalized applicability, then the project not recently covered.
6. A rising claim requires at least two locally recorded observations; label other momentum judgments as inference. Never use raw popularity as a substitute for project quality.
7. Require a successfully archived repository plus substantive README or documentation and inspect relevant code/configuration. If unavailable, fail the evidence gate and produce only a short public-information overview.
8. Read `references/analysis-guide.md`. Write `<workspace>/reports/YYYY-MM-DD/owner--repo-v1.md`, targeting 8,000–12,000 Chinese characters unless explicitly overridden.
9. Explain transferable lessons only when supported by repository evidence. State applicability conditions, costs, risks, and a testable acceptance criterion; do not assume a specific user context unless the current request supplies one.
10. Score the finished report with the output-quality rubric. Require at least the configured passing score and no hard failure. Revise once if it fails; otherwise downgrade rather than padding.
11. Create `<workspace>/reports/YYYY-MM-DD/version-note-v1.md` describing selection, score, evidence, limitations, and changes. Never overwrite a prior long-form report; increment the version.
12. Update `<workspace>/data/daily/YYYY-MM-DD.json` with shortlist scorecards, selection rationale, archive paths, report score, report path, and evidence status.

## Evidence Rules

- Treat README, repository docs, source code, releases, commit history, and repository API metadata as primary evidence.
- Separate facts from interpretation. Attach repository-relative paths or URLs to important factual claims.
- Never convert unavailable source material into a negative fact. Mark it `missing` or `not verified`.
- Build the main conclusion on broadly inspectable evidence. Put low-coverage observations in an exploratory section.
- Avoid reproducing large copyrighted passages. Summarize and quote sparingly.
- Score conservatively. A `5` requires explicit evidence meeting the rubric anchor; uncertainty lowers the score rather than being filled with intuition.

## Cold Storage Contract

Create immutable dated captures under `cold-storage/owner/repo/YYYY-MM-DD/` containing `repository.bundle`, `source/`, `github-api.json`, `manifest.json`, and `key-docs/`. Keep previous captures.

## Failure Handling

- On API rate limits, retain existing observations and report the failure; do not invent candidates.
- On clone/archive failure, record a partial manifest and downgrade the output.
- For exceptionally large repositories, record history limitations and avoid claiming full-history coverage.
- If no candidate passes the evidence threshold, publish a dated candidate brief rather than a 10,000-character report.
