"""Review submission boundaries without printing credentials or private excerpts.

Scans Git candidates, index/history, local evidence and ZIP payloads. No uploads,
staging, deletion, or changes to frozen evidence. Known credentials stay in memory.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PREFIXES = ("results/", "benchmarks/", "configs/", "artifacts/", "docs/", "data/local/")
PUBLIC_EXCEPTIONS = {"docs/README.md", "docs/PRIVACY_REVIEW.md", "artifacts/privacy_review.json"}
PRIVATE_FILE = "report/individual/2A202603399_DongNgocPhuc.md"
SENSITIVE_SUFFIXES = {".pdf", ".zip", ".tar", ".gz", ".sqlite", ".db", ".pem", ".key", ".p12", ".pfx"}
PATTERNS = {
    "openai_key_pattern": re.compile(rb"sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}"),
    "github_token_pattern": re.compile(rb"(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"),
    "aws_access_key_pattern": re.compile(rb"(?:AKIA|ASIA)[A-Z0-9]{16}"),
    "private_key_block": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"),
    "credentialed_database_url": re.compile(rb"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s\"'<>/]+:[^\s\"'<>@]+@"),
}


def git(*args, input=None):
    return subprocess.run(["git", *args], cwd=ROOT, input=input, capture_output=True, check=True).stdout


def private_path(name):
    name = name.replace("\\", "/")
    if name in PUBLIC_EXCEPTIONS:
        return False
    basename = name.rsplit("/", 1)[-1]
    return (name.startswith(PRIVATE_PREFIXES) or name == PRIVATE_FILE
        or (basename.startswith(".env") and basename != ".env.example")
        or any(part in {".aws", ".ssh", ".docker"} for part in name.split("/"))
        or Path(name).suffix.lower() in SENSITIVE_SUFFIXES or basename == ".git-credentials")


def allowed_for_submission(name, full_evidence=False):
    name = name.replace("\\", "/")
    if ".git" in name.split("/"):
        return False
    if not private_path(name):
        return True
    if not full_evidence:
        return False
    if name == "data/submission/day6_handoff.zip":
        return True  # Explicit package, separately scanned member-by-member.
    basename = name.rsplit("/", 1)[-1]
    if (name.startswith("data/local/") or basename.startswith(".env")
            or Path(name).suffix.lower() in SENSITIVE_SUFFIXES
            or any(part in {".git", ".aws", ".ssh", ".docker"} for part in name.split("/"))):
        return False
    return name.startswith(PRIVATE_PREFIXES[:-1]) or name == PRIVATE_FILE


def known_credentials(day6):
    values = []
    config = {}
    if day6:
        from dotenv import dotenv_values
        config = dotenv_values(day6 / "starter/.env")
    for name in ("OPENAI_API_KEY", "DATABASE_URL", "DAY7_RESTORE_DATABASE_URL"):
        for value in (os.environ.get(name), config.get(name)):
            if not value or len(value) < 12:
                continue
            values.append(value.encode())
            if "DATABASE_URL" in name:
                password = urlsplit(value).password
                if password and len(password) >= 8:
                    values.append(password.encode())
    return list(set(values))


def secret_types(data, needles):
    found = [label for label, pattern in PATTERNS.items() if pattern.search(data)]
    # Placeholder example DSNs are permitted; never whitelist actual known credentials.
    if "credentialed_database_url" in found:
        matches = PATTERNS["credentialed_database_url"].findall(data)
        if matches and all(b"USER:PASSWORD@" in m or b"user:password@" in m for m in matches):
            found.remove("credentialed_database_url")
    if any(value in data for value in needles):
        found.append("known_local_credential_exact_match")
    return sorted(set(found))


def scan_git_objects(needles, *, all_refs=False, include_index=True, full_evidence=False):
    scope = ("--all",) if all_refs else ("--branches", "--remotes", "--tags")
    listing = git("rev-list", "--objects", *scope).decode("utf-8").splitlines()
    object_paths = {}
    for line in listing:
        parts = line.split(" ", 1)
        object_paths.setdefault(parts[0], parts[1] if len(parts) > 1 else "(unnamed object)")
    staged = git("ls-files", "--stage", "-z").decode("utf-8").split("\0") if include_index else []
    for line in staged:
        if line:
            metadata, name = line.split("\t", 1)
            object_paths.setdefault(metadata.split()[1], name)
    ids = list(object_paths)
    output = git("cat-file", "--batch", input=("\n".join(ids) + "\n").encode())
    cursor, blobs, findings, private_history = 0, 0, [], []
    for oid in ids:
        end = output.index(b"\n", cursor)
        header = output[cursor:end].decode().split()
        size = int(header[2])
        start = end + 1
        data = output[start:start + size]
        cursor = start + size + 1
        if header[1] != "blob":
            continue
        blobs += 1
        name = object_paths[oid]
        types = secret_types(data, needles)
        if types:
            findings.append({"path": name, "object": oid, "types": types})
        if not allowed_for_submission(name, full_evidence):
            private_history.append({"path": name, "object": oid})
    return {"unique_blobs_scanned": blobs, "secret_findings": findings, "private_path_findings": private_history}


def audit(day6=None):
    needles = known_credentials(day6)
    permission = ROOT / "submission_permission.json"
    full_evidence = permission.is_file() and json.loads(permission.read_text(encoding="utf-8"))["profile"] == "full_lab_evidence"
    candidates = sorted(set(p for p in git("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode("utf-8").split("\0") if p))
    candidate_findings, private_candidates = [], []
    for name in candidates:
        path = ROOT / name
        if not allowed_for_submission(name, full_evidence):
            private_candidates.append(name)
        if path.is_file():
            types = secret_types(path.read_bytes(), needles)
            if types:
                candidate_findings.append({"path": name, "types": types})
    # Scan local/private material too, including archives, without adding it to Git.
    local_findings, scanned, archives, skipped = [], 0, 0, []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".venv", "__pycache__", "tmp"} for part in rel.parts):
            continue
        if path.name.startswith(".env") and path.name != ".env.example":
            continue  # Expected local credential files; separately excluded by Git policy.
        if path.stat().st_size > 30_000_000:
            skipped.append(str(rel))
            continue
        data = path.read_bytes()
        scanned += 1
        types = secret_types(data, needles)
        if types:
            local_findings.append({"path": str(rel), "types": types})
        if path.suffix.lower() == ".zip":
            archives += 1
            with zipfile.ZipFile(path) as archive:
                if sum(i.file_size for i in archive.infolist()) > 100_000_000:
                    skipped.append(str(rel) + " (archive expansion limit)")
                    continue
                for info in archive.infolist():
                    if info.is_dir(): continue
                    types = secret_types(archive.read(info), needles)
                    if types:
                        local_findings.append({"path": str(rel) + "!" + info.filename, "types": types})
    history = scan_git_objects(needles, full_evidence=full_evidence)
    all_refs = scan_git_objects(needles, all_refs=True, include_index=False)
    internal_refs = git("for-each-ref", "--format=%(refname)", "refs/codex/").decode("utf-8").splitlines()
    credentialed_remotes = []
    remotes = subprocess.run(["git", "config", "--get-regexp", r"^remote\..*\.url$"], cwd=ROOT, capture_output=True).stdout.decode("utf-8").splitlines()
    for row in remotes:
        name, url = row.split(" ", 1)
        if url.startswith(("http://", "https://")) and (urlsplit(url).username or urlsplit(url).password):
            credentialed_remotes.append(name)
    private_files = sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in ROOT.rglob("*") if p.is_file()
                           and not any(part in {".git", ".venv", "__pycache__", "tmp"} for part in p.relative_to(ROOT).parts)
                           and not allowed_for_submission(str(p.relative_to(ROOT)), full_evidence))
    ignored = set(p.replace("\\", "/") for p in git("ls-files", "--others", "--ignored", "--exclude-standard", "-z").decode("utf-8").split("\0") if p)
    unprotected = [p for p in private_files if p not in ignored]
    passed = not (candidate_findings or private_candidates or history["secret_findings"] or history["private_path_findings"] or all_refs["secret_findings"] or credentialed_remotes or unprotected or local_findings or skipped)
    public_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in candidates
                     if name != "artifacts/privacy_review.json" and (ROOT / name).is_file()}
    return {"status": "passed" if passed else "needs_review", "sharing_permission": "full lab evidence authorized" if full_evidence else "unconfirmed; source-only Git boundary enforced",
        "git_candidate_count": len(candidates), "git_candidate_secret_findings": candidate_findings,
        "private_git_candidates": private_candidates, "private_files_protected_by_ignore": len(private_files),
        "unprotected_private_paths": unprotected, "local_files_scanned": scanned, "zip_archives_scanned": archives,
        "local_secret_findings": local_findings, "skipped_paths": skipped, "publishable_branch_history_and_index": history,
        "all_local_refs_scan": all_refs, "internal_codex_ref_names": internal_refs,
        "warning": "Only reviewed working files are exported; .git/internal refs are never included. Internal refs were not deleted or rewritten.",
        "credentialed_remote_names": credentialed_remotes, "git_candidate_sha256": public_hashes,
        "limitations": "Pattern and exact-known-credential scan, not proof that no unknown secret exists. No OCR of image/PDF screenshots; raw report/evidence excluded regardless of scan. Ignore rules do not stop git add -f or sanitize past commits. No stage/commit/push/upload performed."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day6-root", type=Path)
    parser.add_argument("--export-source", type=Path, help="Optional local source-only ZIP; refuses private paths/secrets")
    parser.add_argument("--export-full", type=Path, help="Complete evidence ZIP, requires recorded user authorization")
    args = parser.parse_args()
    result = audit(args.day6_root)
    full_output = ROOT / "data/local/privacy_review.full.json"
    full_output.parent.mkdir(parents=True, exist_ok=True)
    full_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    public = {k:v for k,v in result.items() if k not in {
        "all_local_refs_scan", "internal_codex_ref_names", "local_secret_findings", "skipped_paths"}}
    public["all_refs_secret_findings_count"] = len(result["all_local_refs_scan"]["secret_findings"])
    public["internal_snapshot_private_path_count"] = len(result["all_local_refs_scan"]["private_path_findings"])
    public["local_secret_findings_count"] = len(result["local_secret_findings"])
    public["skipped_paths_count"] = len(result["skipped_paths"])
    public["full_local_audit"] = "data/local/privacy_review.full.json (ignored, not in source export)"
    output = ROOT / "artifacts/privacy_review.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.export_source and args.export_full:
        raise SystemExit("Choose one export profile")
    if args.export_source or args.export_full:
        if result["status"] != "passed":
            raise SystemExit("Source export blocked by privacy findings; see local audit")
        full = bool(args.export_full)
        if full and result["sharing_permission"] != "full lab evidence authorized":
            raise SystemExit("Full evidence export requires recorded user authorization")
        destination = (args.export_full or args.export_source).resolve()
        if destination.exists() or not destination.is_relative_to((ROOT / "data/local").resolve()):
            raise SystemExit("Choose a new ZIP under data/local; never overwrite/share automatically")
        paths = sorted(name for name in set(result["git_candidate_sha256"]) | {"artifacts/privacy_review.json"}
                       if allowed_for_submission(name, full))
        if any(not allowed_for_submission(name, full) or name.startswith(".git/") for name in paths):
            raise SystemExit("Private path in source export")
        destination.parent.mkdir(parents=True, exist_ok=True)
        manifest = {"scope": "COMPLETE LAB EVIDENCE, authorized by submission_permission.json" if full else "SOURCE ONLY, not a complete lab submission without authorized private evidence",
                    "excluded": [".git", "credentials", "local scratch/venv"] if full else [".git", "raw report", "benchmark/gold", "traces/reviews", "private report", "vectors/cache", "credentials"],
                    "files_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}
        with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in paths:
                archive.write(ROOT / name, name)
            archive.writestr("SUBMISSION_MANIFEST.json" if full else "SOURCE_ONLY_MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
            if not full:
                archive.writestr("README_SOURCE_ONLY.md", "# Source-only review package\n\nNo .git, report excerpts, gold, traces, PDF, vectors or credentials are included. This is NOT the complete lab submission. Full benchmark/freeze tests require authorized private evidence. Synthetic retrieval checks can run with `python -m unittest discover -s tests -p test_retrieval.py -v`. No upload or commit has been performed.\n")
    print(json.dumps({"status": result["status"], "git_candidates": result["git_candidate_count"],
        "candidate_secret_findings": result["git_candidate_secret_findings"],
        "private_git_candidates": result["private_git_candidates"],
        "private_files_ignored": result["private_files_protected_by_ignore"],
        "local_files_scanned": result["local_files_scanned"], "zip_archives_scanned": result["zip_archives_scanned"],
        "local_secret_findings": result["local_secret_findings"],
        "branch_history_blobs": result["publishable_branch_history_and_index"]["unique_blobs_scanned"],
        "branch_history_secret_findings": result["publishable_branch_history_and_index"]["secret_findings"],
        "branch_history_private_paths": result["publishable_branch_history_and_index"]["private_path_findings"],
        "all_ref_secret_findings": result["all_local_refs_scan"]["secret_findings"],
        "internal_snapshot_private_path_count": len(result["all_local_refs_scan"]["private_path_findings"]),
        "warning": result["warning"]}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "passed" else 1)
