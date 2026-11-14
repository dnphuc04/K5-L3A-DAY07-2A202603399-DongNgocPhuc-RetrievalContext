"""Offline whole-repo audit with historical documents restored in a temp workspace.

Original evaluation receipts, predictor freezes, results and labels stay unchanged.
Historical documentation is verified against its original hashes, then the original
preflight runs on that exact documentation snapshot. Current docs are checked separately.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check():
    from scripts.check_submission import check as basic_check
    from advanced_v2.check_submission import check as current_check
    errors = []
    basic = basic_check()
    current = current_check()
    errors.extend(basic["errors"])
    errors.extend(current["errors"])
    receipt = read(ROOT / "advanced_v2/evaluation_receipt.json")
    amendment = receipt.get("documentation_amendment")
    if amendment:
        previous_path = ROOT / amendment["previous_receipt_snapshot"]
        previous = read(previous_path)
        if sha(previous_path) != amendment["previous_receipt_sha256"]:
            errors.append("Previous receipt snapshot hash mismatch")
        old_doc = ROOT / amendment["previous_document_snapshot"]
        if sha(old_doc) != previous["files_sha256"]["ADVANCED_V2.md"]:
            errors.append("Previous navigation document hash mismatch")
        old_hashes = previous["files_sha256"].copy()
        old_hashes["ADVANCED_V2.md"] = receipt["files_sha256"]["ADVANCED_V2.md"]
        if old_hashes != receipt["files_sha256"]:
            errors.append("Documentation amendment changed other evidence hashes")
        stripped = {k:v for k,v in receipt.items() if k != "documentation_amendment"}
        expected = previous.copy()
        expected["files_sha256"] = old_hashes
        if stripped != expected:
            errors.append("Documentation amendment changed historical receipt fields")
    mapping = read(ROOT / "artifacts/historical_document_map.json")["documents"]
    original = read(ROOT / "advanced/evaluation_receipt.json")["files_sha256"]
    for name, entry in mapping.items():
        if entry["sha256"] != original[name] or sha(ROOT / entry["snapshot"]) != original[name]:
            errors.append("Historical document snapshot mismatch: " + name)
    historical = None
    if not errors:
        with tempfile.TemporaryDirectory(prefix="day7-historical-") as folder:
            target = Path(folder)
            for directory in ("advanced", "src"):
                shutil.copytree(ROOT / directory, target / directory,
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            for name in original:
                if name.startswith(("advanced/", "src/")):
                    continue
                source = ROOT / mapping[name]["snapshot"] if name in mapping else ROOT / name
                output = target / name
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, output)
            program = "import json;from advanced.check_submission import check;r=check();print(json.dumps(r));raise SystemExit(0 if r['technical_evidence_checks_passed'] else 1)"
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            result = subprocess.run([sys.executable, "-c", program], cwd=target,
                                    env=env, capture_output=True, text=True, timeout=90)
            if result.returncode:
                errors.append("Original preflight failed in historical snapshot: " + result.stdout.strip() + result.stderr.strip())
            else:
                historical = json.loads(result.stdout)
    paths = [name for name in subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    ).decode("utf-8").split("\0") if name]
    counts = {"python": 0, "json": 0}
    for name in paths:
        path = ROOT / name
        if not path.is_file():
            continue
        try:
            if path.suffix == ".py":
                compile(path.read_text(encoding="utf-8-sig"), name, "exec")
                counts["python"] += 1
            elif path.suffix == ".json":
                json.loads(path.read_text(encoding="utf-8-sig"))
                counts["json"] += 1
        except (SyntaxError, ValueError, UnicodeError) as exc:
            errors.append(f"Invalid syntax {name}: {exc}")
    for name in ("README.md", "docs/SUBMISSION_CHECKLIST.md", "report/individual/2A202603399_DongNgocPhuc.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        if "29/30" not in text:
            errors.append("Current document missing final score: " + name)
    if "chưa đủ điều kiện 15 điểm bonus" in (ROOT / "README.md").read_text(encoding="utf-8"):
        errors.append("README still presents the old bonus state as current")
    integrity = read(ROOT / "artifacts/basic_result_integrity.json")
    commit = integrity["original_commit"]
    for name in integrity["predictor_inputs_gold_and_raw_traces_byte_identical"]:
        blob = subprocess.check_output(["git", "show", commit + ":" + name], cwd=ROOT)
        if (ROOT / name).read_bytes() != blob:
            errors.append("Original basic predictor/input/raw result changed: " + name)
    return {"checks_passed": not errors, "errors": errors,
            "basic": basic, "advanced_current": current, "advanced_historical_snapshot": historical,
            "syntax_files_checked": counts, "historical_documents_verified": len(mapping),
            "original_evaluation_receipt_unchanged": True,
            "scope": "Offline integrity, syntax, links, metrics and historical-document audit; no API replay or independent score certification."}

if __name__ == "__main__":
    result = check()
    print(json.dumps(result, ensure_ascii=True, indent=2))
    raise SystemExit(0 if result["checks_passed"] else 1)
