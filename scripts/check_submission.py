"""Offline submission preflight: integrity, evidence coverage, links and secret patterns.

Does not publish, claim grader access, certify data rights, or award rubric points.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_agent_test import verify_freezes


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def check():
    errors, checks = [], []
    required = ["README.md", ".gitattributes", "requirements.txt", "requirements-reproduction.txt", ".env.example",
        "report/individual/2A202603399_DongNgocPhuc.md", "docs/SUBMISSION_CHECKLIST.md", "docs/DATA_ACCESS.md",
        "artifacts/day6_audit.json", "artifacts/environment.json", "artifacts/cost_estimate.json", "artifacts/handoff_verification.json",
        "scripts/package_day6.py", "scripts/restore_day6_handoff.py", "results/dev_comparison.json"]
    for name in required:
        if not (ROOT / name).is_file(): errors.append("Missing " + name)
    try:
        verify_freezes()
        checks.append("Frozen predictor, selected config, benchmark and dev evidence unchanged")
    except Exception as exc:
        errors.append("Freeze verification: " + type(exc).__name__)
    receipt = load(ROOT / "results/agent_test_v1/evaluation_receipt.json")
    for name, expected in receipt["sha256"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            errors.append("Test receipt mismatch: " + name)
    counts = {}
    for split, expected in (("dev", (15, 2)), ("test", (5, 2))):
        gold = load(ROOT / f"benchmarks/{split}.gold.json")
        inputs = load(ROOT / f"benchmarks/{split}.inputs.json")
        counts[split] = {"answerable": sum(q["answerable"] for q in gold), "unanswerable": sum(not q["answerable"] for q in gold)}
        if (counts[split]["answerable"], counts[split]["unanswerable"]) != expected:
            errors.append("Benchmark count mismatch: " + split)
        if any(set(q) - {"id", "question", "filter"} for q in inputs): errors.append("Gold leaked into " + split + " inputs")
    reviewed = 0
    for name, expected in (("agent_dev_v1", 51), ("agent_dev_dense_wide", 17), ("agent_dev_dense_wide_quotes", 17), ("agent_test_v1", 14)):
        run = ROOT / "results" / name
        traces = load(run / "traces.json")
        reviews = load(run / "reviews.json")
        trace_ids = {(t["method"], t["query_id"]) for t in traces}
        labels = {(r["method"], r["query_id"]): r for r in reviews["reviews"]}
        if len(traces) != expected or len(trace_ids) != expected or len(labels) != expected or set(labels) != trace_ids:
            errors.append("Incomplete review coverage: " + name)
        if reviews["traces_sha256"] != hashlib.sha256((run / "traces.json").read_bytes()).hexdigest(): errors.append("Stale reviews: " + name)
        for t in traces:
            r = labels[(t["method"], t["query_id"])]
            if not r["reason"] or len(r["citation_support"]) != len(t["citations"]) or len(r["citation_reasons"]) != len(t["citations"]): errors.append("Incomplete label: " + name + "/" + t["query_id"])
        reviewed += len(labels)
    # Check local Markdown links, excluding code fences and ignored private files.
    broken = []
    for path in ROOT.rglob("*.md"):
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".venv", "tmp"} for part in rel.parts) or rel.parts[:2] == ("data", "local"): continue
        text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8-sig"), flags=re.S)
        for target in re.findall(r"\]\(([^)]+)\)", text):
            target = target.strip().split(' "', 1)[0].strip("<>")
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"): continue
            target = target.split("#", 1)[0]
            if target and not (path.parent / target).exists(): broken.append(str(rel) + ": " + target)
    errors.extend("Broken link " + x for x in broken)
    listed = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8").split("\0")
    patterns = [re.compile(r"sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}"), re.compile(r"ghp_[A-Za-z0-9]{30,}"), re.compile(r"github_pat_[A-Za-z0-9_]{30,}")]
    secret_paths = []
    for name in listed:
        path = ROOT / name
        if not name or not path.is_file() or path.suffix.lower() not in {".py", ".json", ".md", ".csv", ".yml", ".yaml", ".example", ".txt"}: continue
        try: text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError: continue
        if any(pattern.search(text) for pattern in patterns): secret_paths.append(name)
    errors.extend("Potential secret pattern in " + p for p in secret_paths)
    if any(Path(name).name.startswith(".env") and Path(name).name != ".env.example" for name in listed if name): errors.append("Non-example dotenv file is included by Git")
    permission_path = ROOT / "submission_permission.json"
    authorized = permission_path.is_file() and load(permission_path).get("profile") == "full_lab_evidence"
    if authorized and not (ROOT / "data/submission/day6_handoff.zip").is_file():
        errors.append("Authorized full submission is missing the data handoff ZIP")
    pending = [] if authorized else ["Confirm permission to hand over report/excerpts", "Give grader private data access"]
    pending += ["Commit/push permitted submission files", "Verify grader access and submit link"]
    result = {"local_checks_passed": not errors, "errors": errors, "checks": checks,
        "benchmark_counts": counts, "reviewed_results": reviewed, "markdown_links_checked": True,
        "secret_scan": "Common OpenAI/GitHub key patterns in tracked and unignored text; no credential values printed. Not a complete privacy/security audit.",
        "handoff_verification": load(ROOT / "artifacts/handoff_verification.json"),
        "full_evidence_authorized": authorized, "external_items_pending": pending,
        "status": "Complete authorized evidence prepared locally; upload/access/submission not yet verified" if authorized else "Technically complete locally; sharing/access/submission steps remain unverified"}
    return result


if __name__ == "__main__":
    result = check()
    (ROOT / "artifacts/submission_check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["local_checks_passed"] else 1)
