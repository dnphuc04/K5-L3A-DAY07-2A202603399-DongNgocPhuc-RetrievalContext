import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "advanced"
LOCAL = ROOT / "data/local/advanced"
PDF = LOCAL / "nasa_systems_engineering_handbook_rev2.pdf"
SOURCE_URL = "https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf"
SOURCE_SHA = "8eeb4887a4dc57a23049da7dd2ed556833cf98e214b240468d987873164ff688"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)

def check_pdf():
    if not PDF.exists() or sha(PDF) != SOURCE_SHA:
        raise ValueError("Download the exact NASA source first; PDF hash mismatch/missing")
