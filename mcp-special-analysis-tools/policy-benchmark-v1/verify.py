"""Mechanical data integrity and cross-format verification; no scientific verdicts."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import tempfile

import jsonschema
import numpy as np
import pandas as pd
import pyreadstat

from generate import HERE, generate, read_typed_csv, sha256, write_json


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def check_hashes(root: Path) -> int:
    manifest = json.loads((root / "manifest.json").read_text())
    for name, expected in manifest["sha256"].items():
        path = (root / name).resolve()
        require(path.is_relative_to(root.resolve()), "Path outside package")
        require(path.is_file() and sha256(path) == expected, f"File hash mismatch: {name}")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name != "manifest.json"}
    if "user_manifest" not in manifest:
        require(actual == set(manifest["sha256"]), "Unlisted or missing package files")
    return len(manifest["sha256"])


def verify_package(path: Path, *, sav_parity=True) -> dict:
    package = json.loads(path.read_text())
    root = path.parent
    jsonschema.Draft4Validator(json.loads((HERE / "schemas/tabular-data-package.json").read_text())).validate(package)
    table_validator = jsonschema.Draft4Validator(json.loads((HERE / "schemas/table-schema.json").read_text()))
    require(package.get("synthetic") is True, "Missing synthetic notice")
    require(package["provenance"]["real_records_used"] is False, "Real-record provenance not declared")
    codebook = json.loads((root / "codebook.json").read_text())["variables"]
    sources = {s["id"] for s in json.loads((root / "sources.json").read_text())["sources"]}
    frames, result = {}, {"id": package["name"], "resources": [], "foreign_keys_checked": 0}
    for resource in package["resources"]:
        schema, name = resource["schema"], resource["name"]
        table_validator.validate(schema)
        source = root / resource["path"]
        require(resource["hash"] == "sha256:" + sha256(source), f"Resource hash: {name}")
        require(resource["bytes"] == source.stat().st_size, f"Resource bytes: {name}")
        fields = schema["fields"]
        frame = read_typed_csv(source, fields)
        frames[name] = frame
        require(len(frame) == resource["rows"], f"Row count: {name}")
        require(len(frame.columns) == resource["columns"], f"Column count: {name}")
        require(len(set(frame.columns.str.lower())) == len(frame.columns), f"Duplicate column: {name}")
        require([v["name"] for v in codebook if v["resource"] == name] == list(frame.columns), f"Codebook alignment: {name}")
        forbidden = {"y0", "y1", "true_effect", "latent_confounder", "propensity_true", "potential_outcome", "oracle"}
        require(not set(frame.columns) & forbidden, f"Oracle leaked into inputs: {name}")
        key = schema.get("primaryKey", [])
        if isinstance(key, str):
            key = [key]
        if key:
            require(not frame[key].isna().any().any(), f"Missing primary key: {name}")
            require(not frame.duplicated(key).any(), f"Duplicate primary key: {name}")
        for f in fields:
            require(f["source_id"] in sources | {"synthetic-design", "derived", "synthetic_only", ""}, f"Unknown source: {name}/{f['name']}")
            require(f.get("title") and f.get("description"), f"Incomplete field description: {name}/{f['name']}")
            if f["type"] in ("integer", "number"):
                observed = frame[f["name"]].dropna().to_numpy(dtype=float)
                require(np.isfinite(observed).all(), f"Non-finite number: {name}/{f['name']}")
                if f["type"] == "integer":
                    require(np.all(observed == np.floor(observed)), f"Non-integer: {name}/{f['name']}")
            if f["value_labels"]:
                declared = {str(k) if f["type"] == "string" else float(k) for k in f["value_labels"]}
                observed = set(frame[f["name"]].dropna())
                require(observed <= declared, f"Unlabelled category: {name}/{f['name']}: {observed - declared}")
        parity = []
        for alternate in resource.get("alternate_formats", []) if sav_parity else []:
            other = root / alternate["path"]
            require(alternate["hash"] == "sha256:" + sha256(other), f"SAV hash: {name}")
            sav, meta = pyreadstat.read_sav(str(other), user_missing=True, apply_value_formats=False)
            require(list(sav.columns) == list(frame.columns) and len(sav) == len(frame), f"SAV shape: {name}")
            for f in fields:
                col = f["name"]
                if f["type"] in ("number", "integer", "boolean"):
                    require(np.allclose(frame[col].to_numpy(dtype=float), sav[col].to_numpy(dtype=float),
                                        rtol=1e-13, atol=1e-12, equal_nan=True), f"SAV value parity: {name}/{col}")
                else:
                    require(frame[col].fillna("").tolist() == sav[col].fillna("").tolist(), f"SAV string parity: {name}/{col}")
                require(meta.column_names_to_labels[col] == f["title"], f"SAV variable label: {name}/{col}")
                convert = str if f["type"] in ("string", "date") else float
                expected = {convert(k): v for k, v in f["value_labels"].items()}
                require(meta.variable_value_labels.get(col, {}) == expected, f"SAV value labels: {name}/{col}")
                expected_missing = {convert(x) for x in f["missing_values"]}
                actual_missing = {r["lo"] for r in meta.missing_ranges.get(col, []) if r["lo"] == r["hi"]}
                require(actual_missing == expected_missing, f"SAV user missing codes: {name}/{col}")
            parity.append("sav:values_labels_user_missing")
        result["resources"].append({"name": name, "rows": len(frame), "columns": len(fields),
                                    "primary_key": key, "format_checks": parity, "sha256": sha256(source)})
    for r in package["resources"]:
        for fk in r["schema"].get("foreignKeys", []):
            left = fk["fields"] if isinstance(fk["fields"], list) else [fk["fields"]]
            ref = fk["reference"]
            right = ref["fields"] if isinstance(ref["fields"], list) else [ref["fields"]]
            target = frames[ref["resource"] or r["name"]]
            require(not target.duplicated(right).any(), f"Non-unique foreign-key target: {r['name']}")
            target_keys = set(target[right].itertuples(index=False, name=None))
            keys = set(frames[r["name"]][left].itertuples(index=False, name=None))
            require(keys <= target_keys, f"Unmatched foreign key: {r['name']}")
            result["foreign_keys_checked"] += 1
    return result


def verify(root: Path, *, regenerate=False) -> dict:
    root = root.resolve()
    count = check_hashes(root) + check_hashes(root / "user") + check_hashes(root / "curator")
    registry = json.loads((root / "user/registry.json").read_text())
    jsonschema.Draft202012Validator(json.loads((HERE / "schemas/registry.schema.json").read_text())).validate(registry)
    ids = [p["id"] for p in registry["packages"]]
    require(len(ids) == len(set(ids)), "Duplicate registry entry")
    require(len(ids) == 12, "Expected six cases with two neutral variants each")
    receipt = dict(scope="mechanical_integrity_only", schema_version="1.0.0", files_hashed=count,
                   scientific_judgment_performed=False, packages=[])
    for entry in registry["packages"]:
        path = root / "user" / entry["entrypoint"]
        for name, expected in entry["metadata_hashes"].items():
            require(sha256(path.parent / name) == expected, f"Registry metadata hash: {name}")
        observed = verify_package(path)
        for r, check in zip(entry["resources"], observed["resources"]):
            require(r["hash"] == "sha256:" + check["sha256"], "Registry resource hash")
        receipt["packages"].append(observed)
    require(not any(p.name in ("dgp.json", "reference_plans.json", "potential_outcomes.csv", "rubric.json")
                    for p in (root / "user").rglob("*")), "Evaluator file in user bundle")
    from evaluation.verify_oracles import verify_oracles
    oracle_checks = verify_oracles(root)
    require(oracle_checks["passed"], "Stored potential-outcome and declared arithmetic identity mismatch")
    receipt["oracle_arithmetic"] = oracle_checks
    if regenerate:
        manifest = json.loads((root / "manifest.json").read_text())
        with tempfile.TemporaryDirectory(prefix="policy-benchmark-regenerate-") as tmp:
            regenerated = Path(tmp) / "generated"
            with_sav = any(root.rglob("*.sav"))
            generate(regenerated, seed=manifest["seed"], with_sav=with_sav)
            paths = [p for p in root.rglob("*") if p.is_file() and p.suffix in (".csv", ".sav")]
            for path in paths:
                other = regenerated / path.relative_to(root)
                require(other.is_file() and sha256(other) == sha256(path), f"CSV/SAV regeneration: {path}")
            receipt["data_regeneration"] = {"files": len(paths), "byte_identical": True, "formats": ["csv", "sav"] if with_sav else ["csv"]}
    receipt["totals"] = {"packages": len(receipt["packages"]),
                          "resources": sum(len(p["resources"]) for p in receipt["packages"]),
                          "resource_rows": sum(r["rows"] for p in receipt["packages"] for r in p["resources"]),
                          "foreign_keys": sum(p["foreign_keys_checked"] for p in receipt["packages"])}
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--regenerate", action="store_true")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    receipt = verify(args.directory, regenerate=args.regenerate)
    if args.receipt:
        write_json(args.receipt, receipt)
    print(json.dumps(receipt["totals"], indent=2))
