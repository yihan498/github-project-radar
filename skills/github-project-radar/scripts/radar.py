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
        item["score"] = (20 if "rising" in item["signals"] else 0) + (8 if "new" in item["signals"] else 0) + (5 if "active" in item["signals"] else 0) + min(12, len(str(item["stars"]))*2)
    candidates = sorted(merged.values(), key=lambda x:(x["score"], x["stars"]), reverse=True)
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
        run(["git","bundle","create",str(dest / "repository.bundle"),"HEAD"], source)
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
        manifest.update(key_docs_bytes=total, status="complete")
    except Exception as e: manifest["limitations"].append("Git archive incomplete: " + str(e))
    save(dest / "manifest.json", manifest); print(dest)

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command", required=True)
    d=sub.add_parser("discover"); d.add_argument("--workspace", required=True); d.set_defaults(fn=discover)
    a=sub.add_parser("archive"); a.add_argument("--workspace", required=True); a.add_argument("--repo", required=True); a.set_defaults(fn=archive)
    args=p.parse_args(); args.fn(args)
if __name__ == "__main__": main()
