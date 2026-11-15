"""Generate the public synthetic mobility survey; no fitted results are stored."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

SEED = 20261115
N = 1800
VERSION = "tutorial-v1"

ATTITUDES = {
    "att_cost": "이동 비용을 꼼꼼히 비교한다",
    "att_convenience": "이동의 편리함을 우선한다",
    "att_environment": "환경 영향을 고려한다",
    "att_safety": "안전 기능을 중요하게 생각한다",
    "att_digital": "디지털 이동 서비스를 쉽게 사용한다",
    "att_transit": "대중교통을 적극적으로 고려한다",
    "att_flexibility": "상황에 따라 이동 수단을 바꾼다",
    "att_ownership": "차량 소유가 필요하다고 생각한다",
}
CHOICES = {
    "choice_commute": ("주된 출퇴근 수단", ["자가용", "대중교통", "도보·자전거", "기타"]),
    "choice_priority": ("이동 수단 선택의 우선 기준", ["비용", "시간", "편의", "환경"]),
    "choice_service": ("향후 이용을 고려할 서비스", ["공유차", "호출차", "대중교통 앱", "없음"]),
    "choice_trip": ("주말의 주된 이동 목적", ["쇼핑", "여가", "가족 방문", "기타"]),
    "choice_info": ("이동 정보를 주로 얻는 곳", ["앱", "웹", "주변 사람", "기타"]),
}


def _by_group(rng: np.random.Generator, group: np.ndarray, rows: list[list[float]]) -> np.ndarray:
    values = np.empty(len(group), dtype=np.int64)
    for klass, probabilities in enumerate(rows):
        selected = group == klass
        values[selected] = rng.choice(np.arange(1, len(probabilities) + 1), selected.sum(), p=probabilities)
    return values


def make_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    segment = rng.choice(2, N, p=[.55, .45])
    income = _by_group(rng, segment, [[.29, .44, .27], [.34, .40, .26]])
    income[rng.random(N) < .035] = 99
    frame = pd.DataFrame({
        "respondent_id": np.arange(1, N + 1),
        "gender": rng.choice([1, 2], N, p=[.51, .49]),
        "age_group": _by_group(rng, segment, [[.22, .28, .30, .20], [.25, .30, .27, .18]]),
        "region": rng.choice([1, 2, 3, 4], N, p=[.26, .31, .23, .20]),
        "income_group": income,
        "household_vehicle": _by_group(rng, segment, [[.30, .56, .14], [.13, .56, .31]]),
        "commute_days": rng.choice([1, 2, 3], N, p=[.19, .57, .24]),
        "survey_weight": np.round(rng.uniform(.72, 1.28, N), 3),
    })
    attitudes = [
        [[.07,.13,.35,.45],[.40,.40,.16,.04]],
        [[.40,.40,.16,.04],[.07,.13,.35,.45]],
        [[.07,.13,.35,.45],[.40,.40,.16,.04]],
        [[.15,.28,.39,.18],[.09,.20,.43,.28]],
        [[.07,.13,.35,.45],[.40,.40,.16,.04]],
        [[.07,.13,.35,.45],[.40,.40,.16,.04]],
        [[.12,.25,.43,.20],[.19,.30,.37,.14]],
        [[.40,.40,.16,.04],[.07,.13,.35,.45]],
    ]
    for name, pattern in zip(ATTITUDES, attitudes):
        frame[name] = _by_group(rng, segment, pattern)
    choices = [
        [[.22,.51,.19,.08],[.69,.17,.07,.07]],
        [[.42,.17,.30,.11],[.15,.23,.51,.11]],
        [[.22,.20,.38,.20],[.30,.27,.18,.25]],
        [[.29,.37,.24,.10],[.25,.30,.35,.10]],
        [[.51,.23,.19,.07],[.29,.31,.30,.10]],
    ]
    for name, pattern in zip(CHOICES, choices):
        frame[name] = _by_group(rng, segment, pattern)
    return frame


def make_codebook() -> dict:
    variables = {
        "respondent_id": {"label": "합성 응답 번호", "role": "id"},
        "gender": {"label": "성별", "value_labels": {"1": "여성", "2": "남성"}},
        "age_group": {"label": "연령대", "value_labels": {"1": "20대", "2": "30대", "3": "40대", "4": "50대 이상"}},
        "region": {"label": "거주 지역", "value_labels": {"1": "서울", "2": "수도권", "3": "광역시", "4": "기타 지역"}},
        "income_group": {"label": "가구 소득 구간", "value_labels": {"1": "낮음", "2": "중간", "3": "높음", "99": "응답 거절"},
                         "missing": [{"kind": "refused", "values": ["99"]}]},
        "household_vehicle": {"label": "가구 차량 대수", "value_labels": {"1": "없음", "2": "1대", "3": "2대 이상"}},
        "commute_days": {"label": "주간 통근 일수", "value_labels": {"1": "0~2일", "2": "3~4일", "3": "5일 이상"}},
        "survey_weight": {"label": "교육용 가중 변수", "role": "weight"},
    }
    scale = {"1": "전혀 그렇지 않다", "2": "그렇지 않은 편", "3": "그런 편", "4": "매우 그렇다"}
    for name, label in ATTITUDES.items():
        variables[name] = {"label": label, "measure": "ordinal", "value_labels": scale}
    for name, (label, options) in CHOICES.items():
        variables[name] = {"label": label, "value_labels": {str(i): value for i, value in enumerate(options, 1)}}
    return {"synthetic": True, "version": VERSION, "variables": variables}


def generate(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Use an empty output directory so files cannot be silently replaced.")
    frame, codebook = make_data(), make_codebook()
    data_csv, data_sav = output / "mobility_survey.csv", output / "mobility_survey.sav"
    book_json, item_csv = output / "codebook.json", output / "item_map.csv"
    frame.to_csv(data_csv, index=False, encoding="utf-8-sig")
    book_json.write_text(json.dumps(codebook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    labels = [spec.get("label", name) for name, spec in codebook["variables"].items()]
    value_labels = {name: {int(code): label for code, label in spec.get("value_labels", {}).items()}
                    for name, spec in codebook["variables"].items() if spec.get("value_labels")}
    pyreadstat.write_sav(frame, data_sav, column_labels=labels,
                         variable_value_labels=value_labels, missing_ranges={"income_group": [99]})
    with item_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["variable", "item_text", "response_code", "response_label"])
        for name, spec in codebook["variables"].items():
            writer.writerow([name, spec.get("label", name), "", ""])
    files = [data_csv, data_sav, book_json, item_csv]
    manifest = {"version": VERSION, "synthetic": True, "seed": SEED, "rows": len(frame),
                "columns": len(frame.columns),
                "generator_versions": {name: version(name) for name in ("numpy", "pandas", "pyreadstat")},
                "license": "CC-BY-4.0",
                "sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
                "notice": "No LCA or MCA estimates are shipped. Run the app to compute results. SAV bytes can differ between runs because its writer adds file metadata; compare decoded values and labels."}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    print(json.dumps(generate(parser.parse_args().output), ensure_ascii=False, indent=2))
