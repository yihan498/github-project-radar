#!/usr/bin/env python3
import argparse, datetime as dt, hashlib, json, os, shutil, subprocess, urllib.parse, urllib.request
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
CONFIG = json.loads((SKILL / "assets" / "config.json").read_text(encoding="utf-8"))

def today(): return dt.datetime.now().astimezone().date().isoformat()
def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
def api(path, params=None):
    url = "https://api.github.com" + path
    if params: url += "?" + urllib.parse.urlencode(params)
    headers = {"Accept":"application/vnd.github+json", "User-Agent":"github-project-radar/1.0", "X-GitHub-Api-Version":"2022-11-28"}
    if os.getenv("GITHUB_TOKEN"): headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45) as r: return json.load(r)
def load_observations(ws):
    p = ws / "data" / "observations.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def discover(args):
    ws, day = Path(args.workspace).resolve(), today()
    cutoff = (dt.date.fromisoformat(day) - dt.timedelta(days=14)).isoformat()
    queries = {
      "new": f"created:>={cutoff} stars:>={CONFIG['minimum_stars']}",
      "active": f"pushed:>={cutoff} stars:>={CONFIG['minimum_stars']}",
      "classic": f"stars:>={CONFIG['classic_minimum_stars']} pushed:>={cutoff}"
    }
    old, merged, errors = load_observations(ws), {}, []
    for signal, query in queries.items():
        try:
            result = api("/search/repositories", {"q":query, "sort":"stars", "order":"desc", "per_page":min(30, CONFIG["daily_candidate_limit"])})
            for item in result.get("items", []):
                if CONFIG["exclude_forks"] and item.get("fork"): continue
                if CONFIG["exclude_archived"] and item.get("archived"): continue
                row = merged.setdefault(item["full_name"], {"repo":item["full_name"], "url":item["html_url"], "description":item.get("description"), "language":item.get("language"), "stars":item["stargazers_count"], "forks":item["forks_count"], "updated_at":item.get("updated_at"), "signals":[]})
                row["signals"].append(signal)
        except Exception as e: errors.append({"signal":signal, "error":str(e)})
    for name, item in merged.items():
        prior = old.get(name, [])
        if prior:
            baseline, delta = prior[-1], item["stars"] - prior[-1]["stars"]
            relative = delta / max(baseline["stars"], 1)
            verified = delta >= CONFIG["rising_absolute_delta"] and relative >= CONFIG["rising_relative_delta"]
            item["growth"] = {"from":baseline["date"], "to":day, "star_delta":delta, "relative_delta":relative, "verified":verified}
            if verified: item["signals"].append("rising")
        else: item["growth"] = {"verified":False, "reason":"first local observation"}
        old.setdefault(name, []).append({"date":day, "stars":item["stars"]}); old[name] = old[name][-90:]
        item["discovery_score"] = (20 if "rising" in item["signals"] else 0) + (8 if "new" in item["signals"] else 0) + (5 if "active" in item["signals"] else 0) + min(12, len(str(item["stars"]))*2)
    candidates = sorted(merged.values(), key=lambda x:(x["discovery_score"], x["stars"]), reverse=True)
    save(ws / "data" / "observations.json", old)
    output = ws / "data" / "candidates" / f"{day}.json"
    save(output, {"date":day, "generated_at":dt.datetime.now().astimezone().isoformat(), "queries":queries, "errors":errors, "candidates":candidates})
    print(output)

def run(command, cwd=None): return subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)
def archive(args):
    ws, day = Path(args.workspace).resolve(), today()
    owner, repo = args.repo.split("/", 1); dest = ws / "cold-storage" / owner / repo / day
    if dest.exists(): print(dest); return
    dest.mkdir(parents=True); manifest = {"repo":args.repo, "captured_at":dt.datetime.now().astimezone().isoformat(), "status":"partial", "limitations":[]}
    try: save(dest / "github-api.json", api(f"/repos/{owner}/{repo}"))
    except Exception as e: manifest["limitations"].append("API metadata unavailable: " + str(e))
    source = dest / "source"
    try:
        run(["git","clone","--filter=blob:none","--no-tags",f"https://github.com/{owner}/{repo}.git",str(source)])
        manifest["commit"] = run(["git","rev-parse","HEAD"], source).stdout.strip()
        try:
            run(["git","bundle","create",str(dest / "repository.bundle"),"HEAD"], source)
        except Exception as e:
            manifest["limitations"].append("Git bundle unavailable: " + str(e))
        files, hashes = [], {}
        for p in source.rglob("*"):
            if p.is_file() and ".git" not in p.parts:
                rel = p.relative_to(source).as_posix(); files.append(rel)
                if p.stat().st_size <= 2_000_000: hashes[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
        manifest.update(file_count=len(files), files=files, sha256=hashes)
        key, total = dest / "key-docs", 0; names = {"readme","license","licence","contributing","security","changelog","changes","code_of_conduct"}
        for p in source.rglob("*"):
            if not p.is_file() or ".git" in p.parts: continue
            rel, size = p.relative_to(source), p.stat().st_size
            wanted = p.stem.lower() in names or (rel.parts and rel.parts[0].lower() in {"docs","doc","documentation"})
            if wanted and size <= CONFIG["archive_key_docs_max_bytes"] and total + size <= CONFIG["archive_total_key_docs_max_bytes"]:
                target = key / rel; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, target); total += size
        manifest.update(key_docs_bytes=total, status="complete" if (dest / "repository.bundle").exists() else "partial")
    except Exception as e: manifest["limitations"].append("Git archive incomplete: " + str(e))
    save(dest / "manifest.json", manifest); print(dest)

CANDIDATE_WEIGHTS = {
    "problem_value": 15, "substance": 15, "transferability": 15,
    "evidence_quality": 15, "engineering": 10, "novelty": 10,
    "community_signal": 8, "risk_transparency": 7, "current_applicability": 5,
}
REPORT_WEIGHTS = {
    "fidelity": 20, "mechanism_depth": 20, "traceability": 15,
    "critical_balance": 10, "general_insights": 15,
    "tailored_improvements": 15, "structure": 5,
}

def validate_dimension(name, value, expected_weight):
    errors = []
    if not isinstance(value, dict): return [f"{name}: must be an object"], 0.0
    raw, weight = value.get("raw"), value.get("weight")
    if not isinstance(raw, int) or isinstance(raw, bool) or not 0 <= raw <= 5:
        errors.append(f"{name}.raw: integer 0..5 required")
    if weight != expected_weight: errors.append(f"{name}.weight: expected {expected_weight}")
    evidence = value.get("evidence")
    if not isinstance(evidence, list) or not evidence: errors.append(f"{name}.evidence: at least one evidence item required")
    if not isinstance(value.get("uncertainty"), str) or not value.get("uncertainty").strip():
        errors.append(f"{name}.uncertainty: explicit uncertainty/counterevidence required")
    return errors, (raw * expected_weight / 5.0 if isinstance(raw, int) and not isinstance(raw, bool) and 0 <= raw <= 5 else 0.0)

def validate_scorecard(args):
    path = Path(args.file).resolve(); card = json.loads(path.read_text(encoding="utf-8")); errors = []
    gates = card.get("hard_gates")
    expected_gates = {"archive_and_access", "source_sufficiency", "license_identified", "basic_safety", "not_recent_duplicate", "growth_claim_valid"}
    if not isinstance(gates, dict): errors.append("hard_gates: object required"); gates = {}
    for name in expected_gates:
        gate = gates.get(name)
        if not isinstance(gate, dict) or not isinstance(gate.get("pass"), bool): errors.append(f"hard_gates.{name}.pass: boolean required")
        if not isinstance(gate, dict) or not isinstance(gate.get("evidence"), list) or not gate.get("evidence"): errors.append(f"hard_gates.{name}.evidence: non-empty list required")
    scores, candidate_total = card.get("candidate_scores"), 0.0
    if not isinstance(scores, dict): errors.append("candidate_scores: object required"); scores = {}
    for name, weight in CANDIDATE_WEIGHTS.items():
        dimension_errors, points = validate_dimension(f"candidate_scores.{name}", scores.get(name), weight)
        errors.extend(dimension_errors); candidate_total += points
    if abs(float(card.get("candidate_total", -999)) - candidate_total) > 0.01: errors.append(f"candidate_total: expected {candidate_total:.2f}")
    report = card.get("report_scores")
    report_total = None
    if report is not None:
        if not isinstance(report, dict): errors.append("report_scores: object or null required")
        else:
            report_total = 0.0
            for name, weight in REPORT_WEIGHTS.items():
                dimension_errors, points = validate_dimension(f"report_scores.{name}", report.get(name), weight)
                errors.extend(dimension_errors); report_total += points
            if abs(float(card.get("report_total", -999)) - report_total) > 0.01: errors.append(f"report_total: expected {report_total:.2f}")
    hard_pass = all(isinstance(gates.get(n), dict) and gates[n].get("pass") is True for n in expected_gates)
    result = {"valid":not errors, "hard_gates_pass":hard_pass, "candidate_total":round(candidate_total,2), "candidate_pass":hard_pass and candidate_total >= CONFIG["candidate_passing_score"], "report_total":round(report_total,2) if report_total is not None else None, "report_pass":None if report_total is None else not card.get("hard_failures") and report_total >= CONFIG["report_passing_score"], "errors":errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors: raise SystemExit(2)

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command", required=True)
    d=sub.add_parser("discover"); d.add_argument("--workspace", required=True); d.set_defaults(fn=discover)
    a=sub.add_parser("archive"); a.add_argument("--workspace", required=True); a.add_argument("--repo", required=True); a.set_defaults(fn=archive)
    v=sub.add_parser("validate-scorecard"); v.add_argument("--file", required=True); v.set_defaults(fn=validate_scorecard)
    args=p.parse_args(); args.fn(args)
if __name__ == "__main__": main()
