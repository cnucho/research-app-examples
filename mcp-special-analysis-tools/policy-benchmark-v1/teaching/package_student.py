"""Build a student handout archive from the exact released ordinary inputs.

This performs file-integrity checks only; it does not select an analysis, produce
an answer, or certify causal validity. No curator files are included.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


HERE = Path(__file__).resolve().parent
VERSION = "policy-analysis-student-v1"
DOCS = ("README_KO.md", "PRACTICE_PROBLEMS_KO.md")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def build(user: Path, output: Path) -> dict:
    user = user.resolve()
    manifest = json.loads((user / "manifest.json").read_text(encoding="utf-8"))
    registry = json.loads((user / "registry.json").read_text(encoding="utf-8"))
    if manifest["version"] != "policy-benchmark-v1" or not manifest["synthetic"]:
        raise ValueError("Expected the policy-benchmark-v1 synthetic ordinary inputs")
    expected = set(manifest["sha256"]) | {"manifest.json"}
    actual = {p.relative_to(user).as_posix() for p in user.rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError("Input file inventory differs from the released manifest")
    payload = {}
    for name in sorted(actual):
        path = user / name
        if path.is_symlink() or not path.resolve().is_relative_to(user):
            raise ValueError("Input contains a symlink or unsafe path")
        raw = path.read_bytes()
        if name != "manifest.json" and sha256(raw) != manifest["sha256"][name]:
            raise ValueError("Input hash mismatch: " + name)
        payload["user/" + name] = raw
    csv_count = 0
    sav_count = 0
    for item in registry["packages"]:
        descriptor_path = user / item["entrypoint"]
        descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
        for resource in descriptor["resources"]:
            raw = (descriptor_path.parent / resource["path"]).read_bytes()
            if "sha256:" + sha256(raw) != resource["hash"]:
                raise ValueError("Data descriptor hash mismatch")
            csv_count += 1
            for alternate in resource.get("alternate_formats", []):
                raw = (descriptor_path.parent / alternate["path"]).read_bytes()
                if "sha256:" + sha256(raw) != alternate["hash"]:
                    raise ValueError("Alternate-format hash mismatch")
                sav_count += alternate["format"] == "sav"
    if (len(registry["packages"]), csv_count, sav_count) != (12, 38, 38):
        raise ValueError("Unexpected released package or data-table counts")
    for name in DOCS:
        payload[name] = (HERE / name).read_bytes()
    package = {
        "version": VERSION,
        "input_release": "policy-benchmark-v1",
        "synthetic": True,
        "no_real_records": True,
        "license": "CC-BY-4.0",
        "policy_questions": 6,
        "input_packages": 12,
        "data_csv_files": csv_count,
        "data_sav_files": sav_count,
        "student_guide": DOCS[0],
        "practice_problems": DOCS[1],
        "registry": "user/registry.json",
        "curator_material_included": False,
        "verification_scope": "Released input bytes and packaging only; not host acceptance or causal validity",
        "sha256": {name: sha256(raw) for name, raw in sorted(payload.items())},
    }
    payload["student-package.json"] = (json.dumps(package, ensure_ascii=False, indent=2) + "\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, raw in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 16, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(payload):
            raise ValueError("Archive verification failed")
        for name, raw in payload.items():
            if archive.read(name) != raw:
                raise ValueError("Archive byte mismatch: " + name)
    return {"version": VERSION, "filename": output.name, "bytes": output.stat().st_size,
            "sha256": sha256(output.read_bytes()), "archive_files": len(payload),
            "input_files": len(actual), "data_csv_files": csv_count, "data_sav_files": sav_count,
            "input_packages": 12, "policy_questions": 6, "curator_material_included": False,
            "verification_scope": package["verification_scope"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("user_directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.user_directory, args.output), ensure_ascii=False, indent=2))
