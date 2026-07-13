---
name: github-project-radar
description: Discover, rank, locally archive, and deeply analyze noteworthy GitHub open-source projects. Use for daily or scheduled GitHub recommendations, fast-rising/new/classic repository discovery, README-and-source-backed project research, local cold storage, and long-form Chinese project analysis explaining what a repository does and what can be learned from it.
---

# GitHub Project Radar

Run a source-first daily research workflow. Produce one strong recommendation rather than many shallow summaries.

## Workflow

1. Use `assets/config.json` as defaults unless the user supplies overrides.
2. Run `python scripts/radar.py discover --workspace <workspace>`. Set `GITHUB_TOKEN` when available; unauthenticated API use has stricter limits.
3. Read `<workspace>/data/candidates/YYYY-MM-DD.json`. Check diversity across `new`, `active`, `classic`, and verified `rising` signals.
4. Select one primary project. A rising claim requires at least two locally recorded observations; label other momentum judgments as inference.
5. Run `python scripts/radar.py archive --workspace <workspace> --repo owner/name` before writing.
6. Require a successfully archived repository plus substantive README or documentation and inspect relevant code/configuration. If unavailable, produce only a short public-information overview and explicitly record the limitation.
7. Read `references/analysis-guide.md` and write `<workspace>/reports/YYYY-MM-DD/owner--repo-v1.md`. Target 8,000–12,000 Chinese characters unless explicitly overridden.
8. Create `<workspace>/reports/YYYY-MM-DD/version-note-v1.md` describing selection, evidence, limitations, and changes. Never overwrite a prior long-form report; increment the version.
9. Update `<workspace>/data/daily/YYYY-MM-DD.json` with selection, signals, archive paths, report path, and evidence status.
10. Verify evidence references, architecture/content structure, limitations, and absence of unsupported growth claims.

## Evidence Rules

- Treat README, repository docs, source code, releases, commit history, and repository API metadata as primary evidence.
- Separate facts from interpretation. Attach repository-relative paths or URLs to important factual claims.
- Never convert unavailable source material into a negative fact. Mark it `missing` or `not verified`.
- Build the main conclusion on broadly inspectable evidence. Put low-coverage observations in an exploratory section.
- Avoid reproducing large copyrighted passages. Summarize and quote sparingly.

## Cold Storage Contract

Create immutable dated captures under `cold-storage/owner/repo/YYYY-MM-DD/` containing `repository.bundle`, `source/`, `github-api.json`, `manifest.json`, and `key-docs/`. Keep previous captures.

## Failure Handling

- On API rate limits, retain existing observations and report the failure; do not invent candidates.
- On clone/archive failure, record a partial manifest and downgrade the output.
- For exceptionally large repositories, record history limitations and avoid claiming full-history coverage.
- If no candidate passes the evidence threshold, publish a dated candidate brief rather than a 10,000-character report.
