"""Bind an execution receipt to checked source bytes, plans and prepared inputs.

This is a mechanical identity check. It neither chooses an analysis nor assesses
causal validity. ``bind_receipt`` returns a new receipt; the CLI atomically saves
it after checking that the existing receipt did not change during verification.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from generate import read_typed_csv, serializable  # noqa: E402


class BindingError(ValueError):
    """A source, reference, input or preserved execution identity differs."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BindingError(message)


def canonical_bytes(value) -> bytes:
    """Use the application's JSON digest convention, including number types."""
    return json.dumps(serializable(value), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def canonical_sha256(value) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    def invalid_number(value):
        raise BindingError(f"Nonfinite JSON number in {path}: {value}")
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=invalid_number)


def inside(base: Path, relative: str) -> Path:
    relative_path = Path(relative)
    require(not relative_path.is_absolute(), f"Expected a relative path: {relative}")
    target = (base / relative_path).resolve()
    require(target.is_relative_to(base.resolve()), f"Path escapes its declared root: {relative}")
    return target


def git_blob_sha1(path: Path) -> str:
    content = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()


def source_binding(app: Path) -> dict:
    manifest_path = HERE / "evaluation/app-source.json"
    manifest = read_json(manifest_path)
    upstream = manifest.get("upstream_commit")
    require(isinstance(upstream, str) and re.fullmatch(r"[0-9a-f]{40}", upstream) is not None,
            "app-source.json must declare an upstream_commit SHA-1")
    declared = manifest.get("files")
    if isinstance(declared, dict):
        declared = [{"path": name, "git_blob_sha1": value} for name, value in declared.items()]
    require(isinstance(declared, list) and bool(declared), "app-source.json has no source files")
    seen, verified = set(), []
    for item in declared:
        relative, expected = item.get("path"), item.get("git_blob_sha1")
        require(isinstance(relative, str) and relative not in seen, "Duplicate or invalid source path")
        require(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{40}", expected) is not None,
                f"Invalid source Git blob SHA-1: {relative}")
        seen.add(relative)
        path = inside(app, relative)
        require(path.is_file(), f"Missing app source file: {relative}")
        actual = git_blob_sha1(path)
        require(actual == expected, f"App source content differs: {relative}; {actual} != {expected}")
        verified.append({"path": relative, "git_blob_sha1": actual, "matches_manifest": True})
    for required in ("policy_analysis/data.py", "r/engine.R"):
        require(required in seen, f"App source manifest does not bind {required}")
    checkout = subprocess.run(["git", "-C", str(app), "rev-parse", "HEAD"],
                              check=True, text=True, capture_output=True).stdout.strip()
    require(re.fullmatch(r"[0-9a-f]{40}", checkout) is not None, "Unexpected app checkout commit")
    return {
        "app_checkout_commit": checkout,
        "app_source_commit": upstream,
        "app_source_binding": {
            "kind": "git_blob_sha1_content",
            "verified": True,
            "manifest": "evaluation/app-source.json",
            "manifest_sha256": file_sha256(manifest_path),
            "upstream_commit": upstream,
            "upstream_tree": manifest.get("upstream_tree"),
            "scope": manifest.get("scope"),
            "matched_files": len(verified),
            "files": verified,
            "checkout_commit_is_source_identity": checkout == upstream,
            "claim": "Listed source bytes match the declared upstream Git blobs; no claim of identical Git history, media, or executable modes.",
        },
    }


def bind_receipt(root: Path, app: Path, evidence: Path) -> dict:
    """Return a receipt bound to this generated root and verified app content.

    ``root`` contains user/registry.json and the corresponding curator tree.
    ``evidence`` contains verification-receipt.json and one directory per run.
    Every current reference preparation is replayed through the content-checked
    app transformation code, using the canonical, explicitly typed CSV inputs.
    No original evidence or input file is changed by this function.
    """
    root, app, evidence = Path(root).resolve(), Path(app).resolve(), Path(evidence).resolve()
    original_receipt = read_json(evidence / "verification-receipt.json")
    receipt = copy.deepcopy(original_receipt)
    binding = source_binding(app)
    engine_sha = file_sha256(app / "r/engine.R")
    require(receipt.get("app_engine_sha256") == engine_sha, "Receipt engine SHA-256 differs from checked app source")

    # Fail instead of silently reusing a module loaded from a different app.
    if str(app) not in sys.path:
        sys.path.insert(0, str(app))
    data_module = importlib.import_module("policy_analysis.data")
    require(Path(data_module.__file__).resolve() == (app / "policy_analysis/data.py").resolve(),
            "policy_analysis.data was imported from a different checkout")
    transform_rows = data_module.transform_rows

    registry = read_json(root / "user/registry.json")
    catalog = {}
    for entry in registry["packages"]:
        package_id = entry["id"]
        require(package_id not in catalog, f"Duplicate package in current registry: {package_id}")
        descriptor_path = inside(root / "user", entry["entrypoint"])
        descriptor = read_json(descriptor_path)
        relative = Path(entry["entrypoint"]).parent
        reference_path = inside(root / "curator", str(relative / "reference_plans.json"))
        reference_list = read_json(reference_path)
        references = {}
        for reference in reference_list:
            require(reference["id"] not in references, f"Duplicate reference plan: {package_id}/{reference['id']}")
            references[reference["id"]] = reference
        resources = {}
        for resource in descriptor["resources"]:
            require(resource["name"] not in resources, f"Duplicate resource: {package_id}/{resource['name']}")
            resources[resource["name"]] = resource
        catalog[package_id] = {"descriptor": descriptor_path, "resources": resources,
                               "references": references, "reference_path": reference_path,
                               "typed_rows": None}

    # Bind retained import evidence to current CSV and SAV bytes as well. Changes
    # to descriptions/codebooks alone do not pretend that data were rerun.
    for record in receipt.get("imports", []):
        require(record["package"] in catalog, f"Imported package is absent: {record['package']}")
        entry = catalog[record["package"]]
        resource = entry["resources"].get(record["resource"])
        require(resource is not None, f"Imported resource is absent: {record['resource']}")
        formats = [{"format": "csv", "path": resource["path"]}, *resource.get("alternate_formats", [])]
        selected = [item for item in formats if item["format"] == record["format"]]
        require(len(selected) == 1, f"Missing or duplicate import format: {record['package']}/{record['resource']}/{record['format']}")
        file = inside(entry["descriptor"].parent, selected[0]["path"])
        require(file_sha256(file) == record["file_sha256"], f"Previously imported file bytes changed: {file}")

    seen_executions = set()
    executions = receipt.get("executions")
    require(isinstance(executions, list) and bool(executions), "Receipt contains no executions")
    for record in executions:
        key = (record["package"], record["reference_plan"])
        require(key not in seen_executions, f"Duplicate execution: {key}")
        seen_executions.add(key)
        require(key[0] in catalog, f"Executed package is absent from current registry: {key[0]}")
        entry = catalog[key[0]]
        reference = entry["references"].get(key[1])
        require(reference is not None, f"Executed reference is absent from current curator plans: {key}")
        tag = key[0] + "." + key[1]
        run_directory = inside(evidence, tag)
        request_path = run_directory / "request.json"
        request_hash = file_sha256(request_path)
        require(request_hash == record["export"]["request_sha256"], f"Exported request file hash differs: {tag}")
        request = read_json(request_path)
        request_plan_hash = canonical_sha256(request["plan"])
        expected_plan_hash = canonical_sha256(reference["plan"])
        require(request["plan"] == reference["plan"] and request_plan_hash == expected_plan_hash,
                f"Executed plan differs from the current curator plan: {tag}")

        if entry["typed_rows"] is None:
            typed_rows = {}
            for name, resource in entry["resources"].items():
                file = inside(entry["descriptor"].parent, resource["path"])
                frame = read_typed_csv(file, resource["schema"]["fields"])
                typed_rows[name] = serializable(frame.to_dict("records"))
            entry["typed_rows"] = typed_rows
        inputs = entry["typed_rows"]
        require(reference["input_resource"] in inputs, f"Unknown reference input resource: {tag}")
        expected_rows = copy.deepcopy(inputs[reference["input_resource"]])
        operations = copy.deepcopy(reference.get("preparation", []))
        if operations:
            prepared = transform_rows(expected_rows, operations, other_datasets=copy.deepcopy(inputs))
            expected_rows = serializable(prepared["rows"])
            require(canonical_sha256(expected_rows) == prepared["lineage"]["output_hash"],
                    f"Reference canonical JSON differs from the application digest: {tag}")
        expected_rows_hash = canonical_sha256(expected_rows)
        analysis_rows_hash = canonical_sha256(request["rows"])
        require(expected_rows_hash == analysis_rows_hash,
                f"Prepared canonical CSV rows differ from executed rows: {tag}; {expected_rows_hash} != {analysis_rows_hash}")
        require(len(expected_rows) == len(request["rows"]) == record["analysis_rows"], f"Analysis row count differs: {tag}")

        result = read_json(run_directory / "result.json")
        require(canonical_sha256(result) == record["result_hash"], f"Exported result identity differs: {tag}")
        require(result["method"] == record["method"] == reference["plan"]["method"], f"Method identity differs: {tag}")
        require(canonical_sha256(result["specification"]) == request_plan_hash, f"Result specification differs: {tag}")
        provenance = result["provenance"]
        require(provenance["engine_source_sha256"] == engine_sha, f"Executed engine source differs: {tag}")
        require(provenance["request_sha256"] == request_hash, f"Result request provenance differs: {tag}")
        for name, expected in provenance.get("runtime_artifact_sha256", {}).items():
            require(file_sha256(inside(app / "r", name)) == expected, f"Executed runtime artifact differs: {tag}/{name}")

        specification = {name: reference[name] for name in ("id", "input_resource", "plan")}
        specification["preparation"] = reference.get("preparation", [])
        record["reference_specification_sha256"] = canonical_sha256(specification)
        record["analysis_request_plan_sha256"] = request_plan_hash
        record["analysis_rows_sha256"] = analysis_rows_hash
        record["reference_binding"] = {
            "current_reference_and_prepared_rows_match": True,
            "reference_file": entry["reference_path"].relative_to(root).as_posix(),
            "request_file": request_path.relative_to(evidence).as_posix(),
            "request_file_sha256": request_hash,
            "canonical_csv_preparation_rows_sha256": expected_rows_hash,
            "preparation_operations": len(operations),
            "analysis_row_count": len(expected_rows),
        }

    receipt.update(binding)
    receipt["reference_binding"] = {
        "verified": True,
        "scope": "Source content, current curator specifications, preserved execution requests/results and prepared canonical CSV rows; no scientific judgment.",
        "canonical_json": {"sort_keys": True, "separators": [",", ":"], "ensure_ascii": False, "allow_nan": False},
        "registry_sha256": file_sha256(root / "user/registry.json"),
        "executions_bound": len(executions),
        "imports_bound": len(receipt.get("imports", [])),
    }
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Generated root containing user/ and curator/")
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    target = args.evidence.resolve() / "verification-receipt.json"
    initial = target.read_bytes()
    updated = bind_receipt(args.root, args.app, args.evidence)
    require(target.read_bytes() == initial, "Receipt changed during binding; refusing to overwrite concurrent verification")
    content = json.dumps(serializable(updated), ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=".binding-", suffix=".json", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(json.dumps({"receipt": str(target), "executions_bound": len(updated["executions"]),
                      "source_files_bound": updated["app_source_binding"]["matched_files"],
                      "app_checkout_commit": updated["app_checkout_commit"],
                      "app_source_commit": updated["app_source_commit"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
