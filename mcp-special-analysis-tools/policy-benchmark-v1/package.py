"""Package verified synthetic inputs separately from evaluator-only material."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from generate import HERE, VERSION, sha256, write_json
from verify import require, verify


def zip_directory(source: Path, target: Path):
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            name = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 16, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def package(root: Path, output: Path, verification: Path) -> dict:
    integrity = verify(root, regenerate=True)
    receipt = json.loads(verification.read_text())
    require(receipt["totals"]["executions"] == 20, "All 20 explicit reference executions must be verified")
    require(set(receipt["totals"]["methods"]) == {"ancova", "did", "matching", "rd", "mediation", "moderation", "regression"},
            "Seven adapter families must be covered")
    observed = {(r["package"], r["resource"], r["format"]): r["file_sha256"] for r in receipt["imports"]}
    registry = json.loads((root / "user/registry.json").read_text())
    expected = {}
    expected_plans = {}
    for p in registry["packages"]:
        descriptor = json.loads((root / "user" / p["entrypoint"]).read_text())
        for r in descriptor["resources"]:
            expected[(p["id"], r["name"], "csv")] = r["hash"].removeprefix("sha256:")
            for alternate in r.get("alternate_formats", []):
                expected[(p["id"], r["name"], alternate["format"])] = alternate["hash"].removeprefix("sha256:")
        plan_path = root / "curator" / Path(p["entrypoint"]).parent / "reference_plans.json"
        for reference in json.loads(plan_path.read_text()):
            specification = {key: reference[key] for key in ("id", "input_resource", "plan")}
            specification["preparation"] = reference.get("preparation", [])
            raw = json.dumps(specification, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
            expected_plans[(p["id"], reference["id"])] = hashlib.sha256(raw).hexdigest()
    require(observed == expected, "Release inputs differ from the CSV/SAV bytes actually exercised over MCP")
    actual_plans = {(e["package"], e["reference_plan"]): e.get("reference_specification_sha256") for e in receipt["executions"]}
    require(len(actual_plans) == len(receipt["executions"]), "Duplicate reference execution in receipt")
    require(actual_plans == expected_plans, "Current plans or preparation differ from the hash-bound verified executions")
    require(receipt.get("app_source_binding", {}).get("verified") is True, "Missing exact upstream execution-source binding")
    require(receipt["app_source_binding"]["manifest_sha256"] == sha256(HERE / "evaluation/app-source.json"), "Execution-source manifest differs from verified binding")
    require(receipt.get("reference_binding", {}).get("verified") is True, "Missing current reference binding")
    require(receipt["reference_binding"]["registry_sha256"] == sha256(root / "user/registry.json"), "Current metadata registry differs from verified binding")
    require(all(e["reference_checks"]["passed"] for e in receipt["executions"]), "Unresolved numerical mismatch")
    output.mkdir(parents=True, exist_ok=True)
    require(not any(output.iterdir()), "Release output directory must be empty")
    zip_directory(root / "user", output / (VERSION + "-inputs.zip"))
    zip_directory(root / "curator", output / (VERSION + "-evaluator.zip"))
    shutil.copyfile(root / "user/registry.json", output / (VERSION + "-registry.json"))
    shutil.copyfile(verification, output / "verification-receipt.json")
    write_json(output / "integrity-receipt.json", integrity)
    assets = {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(output.iterdir()) if p.is_file()}
    result = dict(version=VERSION, synthetic=True, packages=len(registry["packages"]),
                  scenarios=6, license="CC-BY-4.0", assets=assets,
                  default_analysis_input=VERSION + "-inputs.zip", evaluator_only=VERSION + "-evaluator.zip",
                  no_real_records=True, csv_and_sav_match_actual_mcp_receipt=True, reference_plans_match_receipt=True,
                  verification_scope="Numerical and execution consistency; no causal certification",
                  reproducibility="CSV and SAV bytes reproduced under pinned dependencies; SAV header timestamp fixed to version date")
    write_json(output / (VERSION + "-manifest.json"), result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.directory.resolve(), args.output.resolve(), args.verification.resolve()), indent=2))
