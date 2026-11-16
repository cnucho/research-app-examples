"""Build standalone policy-effect assignments from released ordinary inputs.

This performs file-integrity checks only; it does not select an analysis, produce
an answer, grade an assignment, or certify causal validity. No curator files are
included. Observation data, codebooks and data descriptors are preserved;
input README files and their index hashes are explicitly adapted for
tool-independent classroom use.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


HERE = Path(__file__).resolve().parent
VERSION = "policy-analysis-student-v1"
REVISION = 2
DOCS = ("README_KO.md", "PRACTICE_PROBLEMS_KO.md", "SUBMISSION_TEMPLATE_KO.md", "OPTIONAL_TOOLS_KO.md")
HANDBOOK = "policy-effect-exercises-ko.pdf"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def build(user: Path, output: Path, handbook: Path) -> dict:
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
    original_manifest = payload["user/manifest.json"]
    original_registry = payload["user/registry.json"]
    adapted_readmes = []
    for name in sorted(actual):
        if not name.endswith("README.md"):
            continue
        original = payload["user/" + name]
        if name == "README.md":
            revised = (HERE / "DATA_README_KO.md").read_bytes()
        else:
            content = original.decode("utf-8").replace(
                "분석계획과 해석은 호스트 AI가 작성한다.",
                "분석자는 공개 규칙과 수급기록을 근거로 분석계획과 해석을 작성한다.")
            marker, suffix = "## 앱에 요청하는 예", "## 출처와 이용"
            if content.count(marker) != 1 or content.count(suffix) != 1:
                raise ValueError("Unexpected input README structure: " + name)
            before, remainder = content.split(marker, 1)
            _, after = remainder.split(suffix, 1)
            revised = (before + "## 분석 범위\n\n"
                       "이 설명서와 관측자료를 바탕으로 분석전략을 선택하고 그 근거를 설명한다. "
                       "특정 소프트웨어나 AI 사용은 필수 요건이 아니다. "
                       "과제와 제출기준은 압축파일 최상위의 학생 안내와 문제집을 따른다. "
                       "분석방법이나 결과의 정답표는 포함하지 않는다. "
                       "이 가상 사례의 수치를 실제 정책의 효과로 인용할 수 없다.\n\n"
                       + suffix + after).encode("utf-8")
        payload["user/" + name] = revised
        adapted_readmes.append({"path": "user/" + name,
                                "original_sha256": sha256(original),
                                "student_sha256": sha256(revised)})
    if len(adapted_readmes) != 13:
        raise ValueError("Expected one input index and twelve case README adaptations")
    for item in registry["packages"]:
        readme_path = (Path(item["entrypoint"]).parent / "README.md").as_posix()
        item["metadata_hashes"]["README.md"] = sha256(payload["user/" + readme_path])
        for metadata_name, expected_hash in item["metadata_hashes"].items():
            metadata_path = (Path(item["entrypoint"]).parent / metadata_name).as_posix()
            if sha256(payload["user/" + metadata_path]) != expected_hash:
                raise ValueError("Student registry metadata hash mismatch: " + metadata_path)
    payload["user/registry.json"] = (json.dumps(registry, ensure_ascii=False, indent=2) + "\n").encode()
    manifest["student_handout"] = {
        "version": VERSION, "revision": REVISION,
        "original_manifest": "../provenance/original-input-manifest.json",
        "original_manifest_sha256": sha256(original_manifest),
        "changes": "Thirteen README files are adapted; registry README hashes and this manifest are updated. Observation data, codebooks, descriptors, questionnaires, value labels and sources remain unchanged.",
    }
    manifest["sha256"] = {name: sha256(payload["user/" + name])
                          for name in sorted(actual) if name != "manifest.json"}
    payload["user/manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    payload["provenance/original-input-manifest.json"] = original_manifest
    payload["provenance/original-input-registry.json"] = original_registry
    for name in DOCS:
        payload[name] = (HERE / name).read_bytes()
    payload["00_START_HERE.html"] = (HERE / "START_HERE.html").read_bytes()
    pdf = handbook.read_bytes()
    if not pdf.startswith(b"%PDF-"):
        raise ValueError("The handbook must be a rendered PDF")
    payload[HANDBOOK] = pdf
    changed_names = {row["path"][len("user/"):] for row in adapted_readmes} | {"manifest.json", "registry.json"}
    for name in actual - changed_names:
        if payload["user/" + name] != (user / name).read_bytes():
            raise ValueError("Unexpected modification outside input README files: " + name)
    package = {
        "version": VERSION,
        "revision": REVISION,
        "title": "정책효과 분석 연습과제",
        "learning_mode": "standalone_problem_based",
        "required_application": None,
        "tool_choice": "learner_selected",
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
        "submission_template": DOCS[2],
        "optional_tools": DOCS[3],
        "handbook": HANDBOOK,
        "start_page": "00_START_HERE.html",
        "registry": "user/registry.json",
        "curator_material_included": False,
        "provenance": {
            "base_release_files_verified": len(actual),
            "unchanged_input_files": len(actual - changed_names),
            "all_observed_csv_and_sav_preserved": True,
            "all_codebooks_and_data_descriptors_preserved": True,
            "adapted_readmes": adapted_readmes,
            "regenerated_manifest": "user/manifest.json",
            "registry_update": "Only packages[*].metadata_hashes['README.md'] values change; all other registry fields are preserved.",
            "original_registry": "provenance/original-input-registry.json",
            "original_registry_sha256": sha256(original_registry),
            "original_manifest": "provenance/original-input-manifest.json",
            "original_manifest_sha256": sha256(original_manifest),
        },
        "verification_scope": "Original release verified before README adaptation and registry hash updates; all observation data, codebooks, descriptors, questionnaires, value labels and sources preserved. Packaging checks only, not assignment grading, host acceptance, or causal validity.",
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
    return {"version": VERSION, "revision": REVISION, "filename": output.name, "bytes": output.stat().st_size,
            "sha256": sha256(output.read_bytes()), "archive_files": len(payload),
            "input_files": len(actual), "data_csv_files": csv_count, "data_sav_files": sav_count,
            "unchanged_input_files": len(actual - changed_names),
            "adapted_input_readmes": len(adapted_readmes),
            "input_packages": 12, "policy_questions": 6, "curator_material_included": False,
            "verification_scope": package["verification_scope"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("user_directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--handbook", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.user_directory, args.output, args.handbook), ensure_ascii=False, indent=2))
