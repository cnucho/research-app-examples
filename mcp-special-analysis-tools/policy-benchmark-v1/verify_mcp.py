"""Run explicit evaluator plans through the real policy MCP HTTP/R product path.

Requires a separately checked-out compatible app and its R runtime. Inputs are
read from the generated package, never substituted by stored answer tables.
This script measures execution consistency; the AI reviewer grades reasoning.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from urllib.request import Request, urlopen
import zipfile

from generate import HERE, read_typed_csv, serializable, sha256, write_json
from verify import require, verify

OWNER = "synthetic-benchmark-owner"
TOKEN = "synthetic-local-verification-only"


def equal_rows(left, right):
    require(len(left) == len(right), "Imported row count mismatch")
    for i, (a, b) in enumerate(zip(left, right)):
        require(a.keys() == b.keys(), f"Imported columns mismatch at row {i}")
        for key, value in a.items():
            other = b[key]
            if isinstance(value, (float, int)) and not isinstance(value, bool):
                require(isinstance(other, (float, int)) and math.isclose(value, other, rel_tol=1e-13, abs_tol=1e-12),
                        f"Imported numeric mismatch at {i}/{key}")
            else:
                require(value == other, f"Imported value mismatch at {i}/{key}")


class Client:
    def __init__(self, directory):
        from policy_analysis.service import PolicyService
        from policy_server import PolicyHTTPServer
        self.service = PolicyService(directory, signing_key="synthetic-benchmark-signing-key", max_workers=2,
                                     timeout_seconds=600)
        self.server = PolicyHTTPServer(("127.0.0.1", 0), self.service, {TOKEN: OWNER})
        self.base = "http://127.0.0.1:" + str(self.server.server_address[1])
        self.service.public_base_url = self.base
        self.thread = threading.Thread(target=lambda: self.server.serve_forever(poll_interval=.02), daemon=True)
        self.thread.start()
        self.calls = 0

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.service.close()

    def rpc(self, method, params):
        payload = dict(jsonrpc="2.0", id="fixture", method=method, params=params)
        req = Request(self.base + "/mcp", data=json.dumps(payload, ensure_ascii=False, allow_nan=False).encode(),
                      headers={"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN,
                               "MCP-Protocol-Version": "2025-11-25", "Accept": "application/json, text/event-stream"})
        with urlopen(req, timeout=120) as response:
            require(response.status == 200, "HTTP MCP response status")
            body = json.load(response)
        require("error" not in body, f"MCP protocol error: {body}")
        self.calls += 1
        return body["result"]

    def call(self, tool_name, **arguments):
        r = self.rpc("tools/call", dict(name=tool_name, arguments=arguments))
        require(not r.get("isError"), f"{tool_name}: {r}")
        require(json.loads(r["content"][0]["text"]) == r["structuredContent"], "MCP text/structured parity")
        return r["structuredContent"]

    def error(self, tool_name, **arguments):
        r = self.rpc("tools/call", dict(name=tool_name, arguments=arguments))
        require(r.get("isError") is True, f"Expected mechanical rejection: {tool_name}")
        return r["structuredContent"]["error"]

    def rows(self, sid, dataset_id):
        # The full imported immutable memory is read for independent verification;
        # the import, preparation and analysis requests themselves travel over HTTP.
        return self.service.store.get_dataset(OWNER, sid, dataset_id)["rows"]


def execute_plan(client, sid, dataset_id, reference, tag):
    saved = client.call("policy_save_plan", study_id=sid, plan=reference["plan"])
    client.call("policy_record_note", study_id=sid, event_type="ai_decision",
                content={"author": "host_ai_fixture", "reference_plan_id": reference["id"],
                         "rationale": reference["plan"]["rationale"]})
    args = dict(study_id=sid, dataset_id=dataset_id, plan_id=saved["plan_id"], request_id=tag)
    run = client.call("policy_run_analysis", **args)
    deadline = time.monotonic() + 620
    while run["status"] in ("created", "queued", "running") and time.monotonic() < deadline:
        time.sleep(.15)
        run = client.call("policy_get_run", study_id=sid, run_id=run["run_id"])
    require(run["status"] == "completed", f"R execution {tag}: {run.get('error')}")
    require(run["ai_narrative"] is None, "Code generated a narrative")
    require(not {"interpretation", "recommendation", "causal_validity"} & run["result"].keys(), "Code interpreted findings")
    from policy_analysis.service import digest
    require(digest(run["result"]) == run["result_hash"], "Result hash")
    require(run["snapshot"]["plan"] == reference["plan"], "Stored plan identity")
    require(not [c for c in run["verification"]["checks"] if c["comparison"] == "mismatch"],
            f"Product numeric verification mismatches: {run['verification']}")
    duplicate = client.call("policy_run_analysis", **args)
    require(duplicate["run_id"] == run["run_id"], "Idempotent run identity")
    return run


def export_and_check(client, sid, run, output, tag):
    result = run["result"]
    # Authored once by the host as a rendering fixture, not a scientific narrative.
    narrative = {"title": "합성 정책자료 실행 검증", "answer": "이 결과는 가상자료의 계산·보고서 연결을 확인한 실행 기록이다.",
                 "expert_explanation": "정책효과의 해석은 이 수치 정합성 시험에 포함하지 않았다.",
                 "limitations": ["실제 정책 또는 실제 모집단에 대한 결론이 아니다."]}
    charts = [{"id": "canonical-estimates", "type": "coefficient", "title": "합성자료의 명시된 비교 추정치",
               "data_ref": "/estimates", "fields": {"label": "term", "estimate": "estimate", "low": "conf_low", "high": "conf_high"},
               "reference_x": 0}]
    bindings = [{"path": "/estimates/0/estimate", "value": result["estimates"][0]["estimate"]}]
    submitted = client.call("policy_submit_narrative", study_id=sid, run_id=run["run_id"], result_hash=run["result_hash"],
                            narrative=narrative, numeric_bindings=bindings, chart_specifications=charts)
    require(all(c["comparison"] == "match" for c in submitted["numeric_checks"]["checks"]), "Narrative numeric binding")
    bundle = client.call("policy_export_report", study_id=sid, run_id=run["run_id"], include_data=True)
    item = next(a for a in bundle["artifacts"] if a["name"] == "policy_analysis.zip")
    with urlopen(item["url"], timeout=120) as response:
        raw = response.read()
    require(hashlib.sha256(raw).hexdigest() == item["sha256"] and len(raw) == item["bytes"], "Signed report download")
    target = output / tag
    target.mkdir(parents=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        for entry in manifest["files"]:
            b = archive.read(entry["name"])
            require(hashlib.sha256(b).hexdigest() == entry["sha256"], "Report member hash")
            require(entry["result_hash"] == run["result_hash"], "Report result identity")
        require(json.loads(archive.read("result.json")) == result, "Canonical export result")
        html = archive.read("report.html").decode()
        require(narrative["answer"] in html and run["result_hash"] in html, "Report narrative provenance")
        require("report.docx" in archive.namelist() and any(p.endswith(".svg") for p in archive.namelist()), "Report formats")
        # Retain only the request/result needed for a separate numerical reference.
        for name in ("request.json", "result.json"):
            (target / name).write_bytes(archive.read(name))
        required = {"report.html", "report.docx", "manifest.json"}
        for name in archive.namelist():
            if name in required or name.endswith((".svg", ".png")):
                (target / Path(name).name).write_bytes(archive.read(name))
    return {"file_count": len(manifest["files"]), "zip_sha256": item["sha256"],
            "numeric_bindings": len(bindings), "request_sha256": sha256(target / "request.json")}, target


def integrity_probes(client):
    sid = client.call("policy_create_study", question="합성 input-contract probes", title="Mechanical probes")["study_id"]
    ids = ["000001", "900719925474099312345"]
    text = "person_id,score\n" + "\n".join(x + ",1" for x in ids) + "\n"
    imported = client.call("policy_import_dataset", study_id=sid, name="string-identifiers", filename="ids.csv",
                           content_base64=base64.b64encode(text.encode()).decode(),
                           options={"column_types": {"person_id": "string", "score": "integer"}})
    require([r["person_id"] for r in client.rows(sid, imported["dataset_id"])] == ids, "Identifier preservation")
    left = client.call("policy_import_dataset", study_id=sid, name="left", rows=[{"key": "001", "y": 1}, {"key": "002", "y": 2}])
    duplicate = client.call("policy_import_dataset", study_id=sid, name="duplicate", rows=[{"key": "001", "x": 1}, {"key": "001", "x": 2}])
    operation = {"op": "join", "right_dataset": duplicate["dataset_id"], "left_on": "key", "right_on": "key",
                 "how": "left", "cardinality": "m:1"}
    rejected = client.error("policy_transform_dataset", study_id=sid, dataset_id=left["dataset_id"], name="bad-join",
                            operations=[operation], other_dataset_ids=[duplicate["dataset_id"]])
    right = client.call("policy_import_dataset", study_id=sid, name="right", rows=[{"key": "001", "x": 1}])
    operation["right_dataset"] = right["dataset_id"]
    unmatched = client.call("policy_transform_dataset", study_id=sid, dataset_id=left["dataset_id"], name="unmatched-join",
                             operations=[operation], other_dataset_ids=[right["dataset_id"]])
    rows = client.rows(sid, unmatched["dataset_id"])
    require(len(rows) == 2 and sum(r["x"] is None for r in rows) == 1, "Unmatched join count")
    missing = client.call("policy_import_dataset", study_id=sid, name="raw-missing-code", rows=[{"x": 1, "y": -1}, {"x": 2, "y": 3}])
    recoded = client.call("policy_transform_dataset", study_id=sid, dataset_id=missing["dataset_id"], name="explicit-missing",
                          operations=[{"op": "recode", "column": "y", "mapping": [{"from": -1, "to": None}], "unmatched": "keep"}])
    require(client.rows(sid, missing["dataset_id"])[0]["y"] == -1 and client.rows(sid, recoded["dataset_id"])[0]["y"] is None,
            "Missing code transformed without changing original")
    return {"string_identifiers_preserved": ids, "duplicate_join_rejection": rejected,
            "unmatched_left_join_rows": 1, "explicit_missing_recode_preserves_source": True}


def verify_mcp(root: Path, app: Path, output: Path, only: list[str] | None = None):
    sys.path.insert(0, str(app.resolve()))
    from policy_analysis.service import digest
    output.mkdir(parents=True, exist_ok=True)
    require(not any(output.iterdir()), "Verification output directory must be empty")
    integrity = verify(root)
    registry = json.loads((root / "user/registry.json").read_text())
    from evaluation.bind_receipt import source_binding
    app_binding = source_binding(app)
    receipt = dict(scope="actual_authenticated_HTTP_MCP_R_execution", synthetic=True,
                   app_repository="cnucho/mcp-special-analysis-tools", **app_binding,
                   app_engine_sha256=sha256(app / "r/engine.R"), judgment_author="host_ai",
                   mechanical_integrity=integrity["totals"], executions=[], imports=[])
    with tempfile.TemporaryDirectory(prefix="policy-benchmark-service-") as state:
        client = Client(state)
        try:
            initialized = client.rpc("initialize", {"protocolVersion": "2025-11-25", "capabilities": {},
                                                     "clientInfo": {"name": "synthetic-policy-fixture", "version": "1.0.0"}})
            require(initialized["serverInfo"]["version"] == "0.2.0", "Unexpected app version")
            cap = client.call("policy_capabilities")
            receipt["runtime"] = cap["engine"]["runtime"]
            for entry in registry["packages"]:
                if only and not any(key in entry["id"] for key in only):
                    continue
                descriptor_path = root / "user" / entry["entrypoint"]
                descriptor = json.loads(descriptor_path.read_text())
                relative = Path(entry["entrypoint"]).parent
                oracle_root = root / "curator" / relative
                sid = client.call("policy_create_study", question=descriptor["policy_question"], title=entry["id"])["study_id"]
                imported, original_rows = {}, {}
                for resource in descriptor["resources"]:
                    schema = resource["schema"]["fields"]
                    types = {f["name"]: f["type"] if f["type"] in ("integer", "number", "boolean") else "string" for f in schema}
                    source = descriptor_path.parent / resource["path"]
                    expected = serializable(read_typed_csv(source, schema).to_dict("records"))
                    for fmt in [{"format": "csv", "path": resource["path"]}, *resource.get("alternate_formats", [])]:
                        p = descriptor_path.parent / fmt["path"]
                        data = client.call("policy_import_dataset", study_id=sid, name=resource["name"] + "-" + fmt["format"],
                                           filename=p.name, content_base64=base64.b64encode(p.read_bytes()).decode(),
                                           options={"column_types": types, "asserted_metadata": {"synthetic": True, "codebook": schema}})
                        rows = client.rows(sid, data["dataset_id"])
                        equal_rows(expected, rows)
                        observed = client.call("policy_inspect_dataset", study_id=sid, dataset_id=data["dataset_id"], limit=2)
                        require(observed["profile"]["row_count"] == resource["rows"], "MCP inspection count")
                        require(observed["metadata"]["source_sha256"] == sha256(p), "Imported file provenance")
                        receipt["imports"].append({"package": entry["id"], "resource": resource["name"], "format": fmt["format"],
                                                   "rows": len(rows), "file_sha256": sha256(p), "values_match_canonical_csv": True})
                        if fmt["format"] == "csv":
                            imported[resource["name"]] = data["dataset_id"]
                            original_rows[resource["name"]] = rows
                references = json.loads((oracle_root / "reference_plans.json").read_text())
                for reference in references:
                    tag = entry["id"] + "." + reference["id"]
                    print("RUN " + tag, flush=True)
                    dataset_id = imported[reference["input_resource"]]
                    operations = copy.deepcopy(reference.get("preparation", []))
                    other_ids = []
                    for op in operations:
                        if op["op"] == "join":
                            op["right_dataset"] = imported[op["right_dataset"]]
                            other_ids.append(op["right_dataset"])
                    if operations:
                        prepared = client.call("policy_transform_dataset", study_id=sid, dataset_id=dataset_id, name=tag,
                                                operations=operations, other_dataset_ids=list(dict.fromkeys(other_ids)))
                        dataset_id = prepared["dataset_id"]
                    run = execute_plan(client, sid, dataset_id, reference, tag)
                    numeric, target = export_and_check(client, sid, run, output, tag)
                    rscript = os.environ.get("POLICY_RSCRIPT", "Rscript")
                    command = [rscript, "--vanilla", str(HERE / "evaluation/check_reference.R"),
                               str(target / "request.json"), str(target / "result.json")]
                    direct = subprocess.run(command, capture_output=True, text=True, timeout=600)
                    require(direct.returncode == 0, f"Independent R reference {tag}: {direct.stderr}\n{direct.stdout[-4000:]}")
                    reference_checks = json.loads(direct.stdout)
                    require(reference_checks["passed"], f"Independent numerical mismatch {tag}: {reference_checks}")
                    write_json(target / "reference-checks.json", reference_checks)
                    result = run["result"]
                    record = dict(package=entry["id"], reference_plan=reference["id"], method=result["method"],
                                  result_hash=run["result_hash"], analysis_rows=len(client.rows(sid, dataset_id)),
                                  result_estimates=result["estimates"], export=numeric, reference_checks=reference_checks,
                                  realized_settings=result.get("realized_settings"), warnings=result.get("warnings"))
                    if result["method"] == "matching":
                        matched = client.call("policy_extract_matched_sample", study_id=sid, run_id=run["run_id"],
                                              result_hash=run["result_hash"], name="returned-matched-sample",
                                              pair_column="benchmark_pair", row_index_column="benchmark_source_row", weight_column="benchmark_weight")
                        matched_rows, analysis_rows = client.rows(sid, matched["dataset_id"]), client.rows(sid, dataset_id)
                        for row in matched_rows:
                            source = analysis_rows[row["benchmark_source_row"] - 1]
                            require(all(row[k] == v for k, v in source.items()), "Matched extraction changed original values")
                        record["matched_extraction"] = {"rows": len(matched_rows), "pairs": len(result["tables"]["pairs"]),
                                                         "all_original_values_preserved": True}
                        dgp = json.loads((oracle_root / "dgp.json").read_text())
                        link = dgp.get("oracle_link")
                        if link:
                            import csv
                            with (oracle_root / "potential_outcomes.csv").open(encoding="utf-8-sig") as stream:
                                truth = {r[link["oracle_id"]]: float(r[link["effect_column"]]) for r in csv.DictReader(stream)}
                            retained = [analysis_rows[p["treated_row_index"] - 1][link["observed_id"]] for p in result["tables"]["pairs"]]
                            record["retained_treated_finite_sample_target"] = sum(truth[str(x)] for x in retained) / len(retained)
                            record["target_comparison_rule"] = "Recorded for reviewer; no equality-to-estimate assertion"
                    # All source versions must survive preparation unchanged.
                    for name, source_rows in original_rows.items():
                        require(client.rows(sid, imported[name]) == source_rows, "Preparation mutated source")
                    receipt["executions"].append(record)
                    write_json(output / "verification-receipt.json", receipt)
                    print("PASS " + tag + " / " + str(len(reference_checks["checks"])) + " numeric checks", flush=True)
            receipt["integrity_probes"] = integrity_probes(client)
            receipt["http_calls"] = client.calls
        finally:
            client.close()
    receipt["totals"] = dict(imports=len(receipt["imports"]), executions=len(receipt["executions"]),
                              methods=sorted({e["method"] for e in receipt["executions"]}),
                              numerical_checks=sum(len(e["reference_checks"]["checks"]) for e in receipt["executions"]))
    write_json(output / "verification-receipt.json", receipt)
    from evaluation.bind_receipt import bind_receipt
    receipt = bind_receipt(root, app, output)
    write_json(output / "verification-receipt.json", receipt)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--only", action="append")
    args = parser.parse_args()
    result = verify_mcp(args.directory.resolve(), args.app.resolve(), args.output.resolve(), args.only)
    print(json.dumps(result["totals"], indent=2))
