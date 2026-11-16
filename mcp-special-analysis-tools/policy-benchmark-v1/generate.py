"""Create versioned, entirely synthetic policy research inputs and separate oracles.

The scientific designs and reference plans are explicitly authored in cases/.
This writer performs serialization, metadata generation and checksums only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
from importlib.metadata import version
from pathlib import Path
import platform
import shutil

import pandas as pd
import pyreadstat

from fixturelib import SEED, VERSION, serializable

HERE = Path(__file__).resolve().parent
CASE_MODULES = ["c01_heat_panel", "c02_youth_transport", "c03_training",
                "c04_insulation_rd", "c05_digital_mediation", "c06_heat_moderation"]
LICENSE = {"name": "CC-BY-4.0", "path": "https://creativecommons.org/licenses/by/4.0/",
           "title": "Creative Commons Attribution 4.0 International"}
NOTICE = ("SYNTHETIC: 모든 관측값·개인·지역·사업 규칙·문항은 가상이다. "
          "실제 응답자나 행정기록을 변형한 자료가 아니다. 공식 자료는 구조 참고에만 사용했다.")
RELEASE = "https://github.com/cnucho/research-app-examples/releases/tag/policy-benchmark-v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(serializable(obj), ensure_ascii=False, indent=2,
                               allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig", lineterminator="\n",
                 float_format="%.15g")


def normalize_sav_timestamp(path: Path) -> None:
    """Use the benchmark's declared version date, not the wall clock.

    SPSS system-file header: date is bytes 92:101, time is 101:109.
    No dictionary, case or other metadata byte is changed. Layout reference:
    https://www.gnu.org/software/pspp/pspp-dev/html_node/File-Header-Record.html
    """
    data = bytearray(path.read_bytes())
    if data[:4] != b"$FL2" or len(data) < 176:
        raise ValueError("Unexpected SAV header; timestamp normalization refused")
    data[92:109] = b"16 Nov 2600:00:00"
    path.write_bytes(data)


def read_typed_csv(path: Path, fields: list[dict]) -> pd.DataFrame:
    """Preserve identifiers and declared codes; do not infer missing-data policy."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != [f["name"] for f in fields]:
            raise ValueError(f"Header mismatch: {path}")
        rows = list(reader)
    for row in rows:
        for f in fields:
            text = row[f["name"]]
            if text == "":
                row[f["name"]] = None
            elif f["type"] == "integer":
                row[f["name"]] = int(text)
            elif f["type"] == "number":
                row[f["name"]] = float(text)
            elif f["type"] == "boolean":
                if text not in ("True", "False", "true", "false", "1", "0"):
                    raise ValueError(f"Invalid declared boolean in {path}")
                row[f["name"]] = text.lower() in ("true", "1")
    return pd.DataFrame(rows, columns=[f["name"] for f in fields])


def emit_resource(root: Path, r: dict, with_sav: bool) -> dict:
    path = root / "data" / (r["name"] + ".csv")
    write_csv(path, r["frame"])
    schema = {"fields": serializable(r["fields"]), "missingValues": [""]}
    if r["primary_key"]:
        schema["primaryKey"] = r["primary_key"]
    if r["foreign_keys"]:
        schema["foreignKeys"] = r["foreign_keys"]
    desc = dict(name=r["name"], title=r["title"], profile="tabular-data-resource",
                path=path.relative_to(root).as_posix(), format="csv", mediatype="text/csv",
                encoding="utf-8-sig", dialect={"delimiter": ",", "header": True, "doubleQuote": True, "quoteChar": "\""},
                schema=schema, rows=len(r["frame"]), columns=len(r["fields"]),
                bytes=path.stat().st_size, hash="sha256:" + sha256(path))
    if "description" in r:
        desc["description"] = r["description"]
    if with_sav:
        # Encode exactly the canonical decimal CSV, not a different precision copy.
        frame = read_typed_csv(path, r["fields"])
        labels, missing, measures = {}, {}, {}
        for f in r["fields"]:
            name, kind = f["name"], f["type"]
            convert = str if kind in ("string", "date") else float
            if f["value_labels"]:
                labels[name] = {convert(k): str(v) for k, v in f["value_labels"].items()}
            if f["missing_values"]:
                missing[name] = [convert(x) for x in f["missing_values"]]
            measures[name] = f.get("measure", "nominal" if kind == "string" or f["value_labels"] else "scale")
            if kind in ("string", "date"):
                frame[name] = frame[name].fillna("").astype(str)
            elif kind == "boolean":
                frame[name] = frame[name].astype(float)
        sav_path = path.with_suffix(".sav")
        pyreadstat.write_sav(frame, str(sav_path), file_label="SYNTHETIC policy benchmark v1",
                            column_labels={f["name"]: f["title"] for f in r["fields"]},
                            variable_value_labels=labels, missing_ranges=missing,
                            variable_measure=measures)
        normalize_sav_timestamp(sav_path)
        desc["alternate_formats"] = [{"format": "sav", "path": sav_path.relative_to(root).as_posix(),
                                       "bytes": sav_path.stat().st_size,
                                       "hash": "sha256:" + sha256(sav_path),
                                       "parity": "typed_values_and_declared_missing_codes"}]
    return desc


def emit_codebooks(root: Path, case: dict, variant: dict) -> None:
    variables, questions, mappings, values = [], [], [], []
    for r in variant["resources"]:
        for f in r["fields"]:
            item = {"resource": r["name"], **serializable(f)}
            variables.append(item)
            if f.get("question"):
                questions.append({"resource": r["name"], "variable": f["name"],
                                  "question": f["question"], "response_type": f["type"],
                                  "response_codes": json.dumps(f["value_labels"], ensure_ascii=False),
                                  "universe": f.get("universe", case["target_population"]),
                                  "time_reference": f["time_reference"],
                                  "skip_condition": f.get("skip_condition", "없음"),
                                  "wording_origin": "새로 작성한 합성 문항; 공식 조사문항/검증척도 아님"})
            mappings.append({"resource": r["name"], "variable": f["name"],
                             "source_id": f["source_id"], "source_variable": f["source_variable"],
                             "source_match": f["source_match"], "synthetic_unit": f["unit"],
                             "synthetic_values_only": True})
            for k, v in f["value_labels"].items():
                values.append({"resource": r["name"], "variable": f["name"], "code": k, "label": v,
                               "user_missing": str(k) in {str(x) for x in f["missing_values"]}})
    write_json(root / "codebook.json", {"synthetic": True, "version": VERSION, "notice": NOTICE,
                                        "variables": variables})
    flat = []
    columns = ["resource", "name", "title", "type", "description", "role", "unit", "value_labels",
               "missing_values", "time_reference", "question", "universe", "skip_condition",
               "derived_from", "derivation_formula", "source_id", "source_variable", "source_match"]
    for v in variables:
        flat.append({k: json.dumps(v[k], ensure_ascii=False) if isinstance(v.get(k), (dict, list))
                     else v.get(k, "") for k in columns})
    write_csv(root / "codebook.csv", pd.DataFrame(flat, columns=columns))
    write_csv(root / "questionnaire.csv", pd.DataFrame(questions, columns=["resource", "variable", "question",
              "response_type", "response_codes", "universe", "time_reference", "skip_condition", "wording_origin"]))
    write_csv(root / "source_crosswalk.csv", pd.DataFrame(mappings))
    write_csv(root / "value_labels.csv", pd.DataFrame(values, columns=["resource", "variable", "code", "label", "user_missing"]))


def write_case_readme(path: Path, case: dict, v: dict, resources: list[dict]) -> None:
    table = "\n".join(f"| `{r['path']}` | {r['title']} | {r['rows']:,} | {r['columns']} | `{' + '.join(r['schema'].get('primaryKey', []))}` |" for r in resources)
    notes = case.get("collection_notes", [])
    if isinstance(notes, str):
        notes = [notes]
    notes = [*notes, *v.get("collection_notes", [])]
    relations = v.get("relationships", [])
    rel_text = "\n".join("- " + json.dumps(x, ensure_ascii=False) for x in relations) or "독립 파일이며 결합할 추가 파일이 없다."
    text = f"""# {case['title']} · {v['id']}

**{NOTICE}**

## 정책 담당자의 질문

{case['policy_question']}

{case['introduction']}

## 수집 범위와 관측 단위

- 대상: {case['target_population']}
- 관측 단위: {case['unit_of_observation']}
- 시간 구조: {case['time_structure']}
- 자료형과 코드는 `datapackage.json`과 `codebook.csv`에 명시했다. 문자열 ID의 앞자리 0을 보존한다.
- 빈 셀은 시스템 결측이다. 변수별 숫자 결측코드는 `missing_values`에 별도로 기록했다. 코드 제거·표본 제외·대체는 분석자가 명시해야 한다.

## 파일 설명

| 파일 | 내용 | 행 | 열 | 기본키 |
| --- | --- | ---: | ---: | --- |
{table}

CSV가 정본이며 SPSS SAV가 제공되면 같은 관측값·변수 라벨·값 라벨·사용자 결측을 담는다. SAV 헤더의 작성시각은 재현을 위해 이 자료 버전 날짜인 2026-11-16 00:00:00으로 고정했다. 실제 실행시각이 아니다. 파일 식별은 배포본 SHA-256, 값 일치는 자료형을 적용한 관측값으로 확인한다.

## 수집·결합 시 알아야 할 사항

""" + "\n".join("- " + n for n in notes) + f"""

### 파일 간 관계

{rel_text}

## 함께 제공하는 설명

`codebook.csv/json`: 변수 설명·단위·시점·역할·결측. `questionnaire.csv`: 새로 작성한 질문과 응답 형식. 행정기록 필드는 설문문항으로 가장하지 않는다. `value_labels.csv`: 범주코드. `source_crosswalk.csv`와 `sources.json`: 실제 자료와 구조가 같은 부분, 별칭·개념 차용·자체 설계의 구분.

## 앱에 요청하는 예

> {case['policy_question']} 이 파일과 설명서를 먼저 확인하고, 비교할 수 있는 대안을 설명해 줘. 필요한 결합·파생변수의 계산 근거를 남기고 결과의 한계도 알려 줘.

분석 방법이나 통계 결과를 미리 정한 답안은 이 입력 묶음에 포함하지 않았다. 정책효과 여부와 인과적 해석은 데이터 생성기가 판단하지 않는다. 이 가상 사례에서 관측된 결과를 실제 정책의 효과로 인용할 수 없다.

## 출처와 이용

실제 관측값은 사용하지 않았다. 공식 설명서·공개 항목은 자료 구조 참고용이며 원문 설문이나 원자료를 재배포하지 않는다. 합성자료와 새 문항은 CC BY 4.0. 표기: cnucho, *Research App Examples: Synthetic Policy Benchmarks*, `policy-benchmark-v1`, `{case['id']}/{v['id']}`. 변경한 경우 변경 사실을 적는다.
"""
    path.write_text(text, encoding="utf-8")


def build_cases(seed: int) -> list[dict]:
    return [importlib.import_module("cases." + m).build(seed + i * 1000)
            for i, m in enumerate(CASE_MODULES)]


def generate(output: Path, seed: int = SEED, with_sav: bool = True) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Use an empty output directory; existing data will not be overwritten.")
    sources_doc = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))
    sources = {s["id"]: s for s in sources_doc["sources"]}
    entries, curator_entries = [], []
    for case in build_cases(seed):
        for v in case["variants"]:
            relative = Path(case["id"]) / v["id"]
            user = output / "user" / relative
            curator = output / "curator" / relative
            user.mkdir(parents=True)
            curator.mkdir(parents=True)
            resources = [emit_resource(user, r, with_sav) for r in v["resources"]]
            emit_codebooks(user, case, v)
            used_ids = set(case["source_ids"]) | {f["source_id"] for r in v["resources"] for f in r["fields"]}
            used_ids -= {"synthetic-design", "derived", "synthetic_only", ""}
            missing_sources = used_ids - sources.keys()
            if missing_sources:
                raise ValueError(f"Unregistered sources: {sorted(missing_sources)}")
            selected_sources = [sources[s] for s in sorted(used_ids)]
            write_json(user / "sources.json", {"real_records_used": False, "sources": selected_sources})
            descriptor = dict(profile="tabular-data-package", name="policy-" + case["id"] + "-" + v["id"],
                              version="1.0.0", title=case["title"], description=case["introduction"],
                              synthetic=True, notice=NOTICE, policy_question=case["policy_question"],
                              target_population=case["target_population"], unit_of_observation=case["unit_of_observation"],
                              time_structure=case["time_structure"], resources=resources,
                              relationships=v.get("relationships", []), licenses=[LICENSE],
                              sources=[{"title": s["title"], "path": s["url"]} for s in selected_sources],
                              metadata={"codebook": "codebook.json", "codebook_csv": "codebook.csv",
                                        "questionnaire": "questionnaire.csv", "source_crosswalk": "source_crosswalk.csv",
                                        "value_labels": "value_labels.csv", "source_notes": "sources.json"},
                              provenance={"real_records_used": False, "schema_similarity": "explicit_per_field",
                                          "generation_version": VERSION, "seed": v["seed"]},
                              ingestion={"type_inference": "disabled; use declared field types",
                                         "missing_policy": "preserve raw codes until an explicit analysis decision"})
            write_json(user / "datapackage.json", descriptor)
            write_case_readme(user / "README.md", case, v, resources)
            oracle = v["evaluator"]
            for name, value in oracle.items():
                if isinstance(value, pd.DataFrame):
                    write_csv(curator / (name + ".csv"), value)
                else:
                    write_json(curator / (name + ".json"), value)
            entry = dict(id="policy." + case["id"] + "." + v["id"], version="1.0.0", synthetic=True,
                         title=case["title"], purpose=["application_development", "integration_testing", "analysis_guidance_evaluation", "teaching"],
                         policy_question=case["policy_question"], observation_unit=case["unit_of_observation"],
                         population=case["target_population"], time_structure=case["time_structure"],
                         entrypoint=(relative / "datapackage.json").as_posix(),
                         documentation=(relative / "README.md").as_posix(),
                         formats=["csv", "sav"] if with_sav else ["csv"],
                         resources=[{k: r[k] for k in ("name", "path", "rows", "columns", "hash")} for r in resources],
                         metadata_hashes={p.name: sha256(p) for p in sorted(user.iterdir()) if p.is_file()},
                         generation={"seed": v["seed"], "version": VERSION, "real_records_used": False},
                         source_ids=sorted(used_ids), license="CC-BY-4.0",
                         compatible_apps=[{"repository": "cnucho/mcp-special-analysis-tools", "version": "0.2.0"}],
                         limitations=["합성자료이며 실제 모집단·정책효과를 대표하지 않는다.",
                                      "참고자료의 원본 스키마 완전 복제품이 아니다; 변수별 대응 범위를 확인한다."])
            entries.append(entry)
            curator_entries.append(dict(id=entry["id"], user_entrypoint=(Path("../user") / relative / "datapackage.json").as_posix(),
                                         oracle_directory=relative.as_posix(),
                                         reference_plans=(relative / "reference_plans.json").as_posix(),
                                         seed=v["seed"]))
    write_json(output / "user" / "registry.json", dict(schema_version="1.0.0", catalog="synthetic-policy-inputs",
                                                       synthetic=True, packages=entries))
    write_json(output / "curator" / "registry.json", dict(schema_version="1.0.0", audience="evaluator_only",
                                                          packages=curator_entries))
    shutil.copyfile(HERE / "manual-ko.md", output / "user" / "README.md")
    shutil.copyfile(HERE / "evaluation" / "README.md", output / "curator" / "README.md")
    for subtree in ("user", "curator"):
        shutil.copyfile(HERE / "LICENSE-DATA.md", output / subtree / "LICENSE-DATA.md")
        files = {p.relative_to(output / subtree).as_posix(): sha256(p)
                 for p in sorted((output / subtree).rglob("*")) if p.is_file()}
        write_json(output / subtree / "manifest.json", dict(version=VERSION, synthetic=True, seed=seed,
                   generator_versions={"python": platform.python_version(), **{x: version(x) for x in ("numpy", "pandas", "pyreadstat")}},
                   license="CC-BY-4.0", sha256=files, notice=NOTICE,
                   reproducibility="CSV and SAV byte-checked under pinned dependencies; SAV header date/time normalized to version date 2026-11-16 00:00:00"))
    manifest = dict(version=VERSION, synthetic=True, seed=seed, packages=len(entries), scenarios=len(CASE_MODULES),
                    release=RELEASE, user_manifest="user/manifest.json", curator_manifest="curator/manifest.json",
                    sha256={"user/manifest.json": sha256(output / "user" / "manifest.json"),
                            "curator/manifest.json": sha256(output / "curator" / "manifest.json")})
    write_json(output / "manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--csv-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(generate(args.output.resolve(), args.seed, not args.csv_only), indent=2))
