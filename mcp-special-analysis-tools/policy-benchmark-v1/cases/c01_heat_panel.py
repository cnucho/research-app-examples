"""Explicitly authored municipal heat-shelter panel fixtures.

Only ``evaluator`` contains potential outcomes and simulation assumptions.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from fixturelib import field, plan, resource


def _variant(seed: int, variant_id: str, differential_trend: float) -> dict:
    rng = np.random.default_rng(seed)
    n_regions = 48
    years = list(range(2017, 2025))
    cohorts = np.repeat([0, 2020, 2021, 2022], 12)
    rng.shuffle(cohorts)
    population = rng.integers(65000, 230001, n_regions)
    elder_share = rng.uniform(12, 31, n_regions)
    area_baseline = rng.normal(0, 3.5, n_regions)
    climate = rng.normal(0, 1.4, n_regions)
    rows, schedules, facilities, potentials = [], [], [], []
    for i in range(n_regions):
        region_id, region_code = i + 1, f"HX{i + 1:03d}"
        cohort = int(cohorts[i])
        schedules.append({"region_code": region_code, "first_treat_year": cohort,
                          "extra_weekly_open_hours": 14 if cohort else 0,
                          "policy_name": "가상 무더위쉼터 야간·휴일 운영지원"})
        for j in range(int(rng.integers(3, 7))):
            facilities.append({"shelter_id": f"{region_code}-S{j + 1:02d}",
                               "region_code": region_code, "inventory_year": 2016,
                               "capacity_persons": int(rng.integers(25, 101)),
                               "air_conditioner_count": int(rng.integers(1, 5))})
        for year in years:
            t = year - 2017
            active = int(cohort > 0 and year >= cohort)
            event_time = year - cohort if cohort else None
            heat_days = max(1, int(round(16 + 1.1 * t + climate[i] + rng.normal(0, 2))))
            # Population remains fixed so the count-to-rate transform is exact.
            # The exposure-independent mean rate has a common time slope in v01.
            untreated_rate_mean = (34 + .42 * elder_share[i] + area_baseline[i]
                                   + .9 * t + .65 * (heat_days - 16)
                                   + differential_trend * int(cohort > 0) * t)
            y0_count = int(rng.poisson(untreated_rate_mean * population[i] / 100000))
            # A finite count contrast is defined explicitly, rather than assuming
            # the realized sample estimate equals a population coefficient.
            rate_reduction = (4.0 + 1.25 * min(event_time, 3)) if active else 0.0
            prevented = min(y0_count, int(round(rate_reduction * population[i] / 100000)))
            y1_count = y0_count - prevented
            observed_count = y1_count if active else y0_count
            y0, y1 = y0_count / population[i] * 100000, y1_count / population[i] * 100000
            rows.append({"region_id": region_id, "region_code": region_code,
                         "year": year, "population": int(population[i]),
                         "heat_reported_cases": observed_count, "heat_days": heat_days,
                         "elder_share_2016": round(float(elder_share[i]), 4)})
            potentials.append({"region_id": region_id, "region_code": region_code,
                               "year": year, "first_treat_year": cohort,
                               "event_time": event_time, "treatment": active,
                               "y0": float(y0), "y1": float(y1),
                               "unit_effect": float(y1 - y0),
                               "observed": float(y1 if active else y0),
                               "y0_reported_count": y0_count,
                               "y1_reported_count": y1_count,
                               "untreated_rate_mean": float(untreated_rate_mean)})
    outcome = pd.DataFrame(rows)
    schedule = pd.DataFrame(schedules)
    facility = pd.DataFrame(facilities)
    potential = pd.DataFrame(potentials)
    region_field = lambda: field("region_code", "string", "가상 지역코드", role="key",
                                 source="heat-shelters", source_variable="지역코드",
                                 match="semantic_alias",
                                 description="HX001–HX048은 자체 부여한 허구 코드다. 실제 행정구역 코드가 아니며 문자열로 보존한다.")
    fk = [{"fields": ["region_code"], "reference": {"resource": "policy_schedule", "fields": ["region_code"]}}]
    resources = [
        resource("annual_outcomes", "가상 지역별 연간 온열질환 감시 신고", outcome, [
            field("region_id", "integer", "가상 지역 일련번호", role="id", description="동일 지역을 8년간 추적하는 숫자 식별자. region_code와 일대일 대응한다."),
            region_field(),
            field("year", "integer", "감시 연도", role="time", unit="년", time="해당 연도 여름 감시기간"),
            field("population", "integer", "가상 지역 인구", role="denominator", unit="명", description="분모 재현을 위한 합성 기준인구. 본 패키지에서는 지역 내 연도별로 고정한다."),
            field("heat_reported_cases", "integer", "온열질환 감시체계 신고 건수", role="outcome", unit="명",
                  source="kdca-heat", source_variable="온열질환자", match="semantic_alias",
                  description="증상 발생 지역·연도에 귀속시킨 합성 표본감시 신고 건수. 전수 발생자 수 또는 진정한 발생률이 아니다."),
            field("heat_days", "integer", "가상 여름 폭염일수", role="context", unit="일", description="연구연습용 자체 생성 날씨 요약량. 특정 관측소의 실측값을 복제하지 않았다."),
            field("elder_share_2016", "number", "도입 전 고령인구 비율", role="pre_treatment_covariate", unit="%", time="2016년", description="2016년 65세 이상 인구 비율의 합성 값. 정책 도입 후 측정값이 아니다."),
        ], primary_key=["region_code", "year"], foreign_keys=fk,
                 description="48개 허구 지역의 2017–2024년 균형 패널. 개인 수준 추적자료가 아니다. 결측은 없고 0건은 관측된 0이다."),
        resource("policy_schedule", "가상 운영지원 도입 이력", schedule, [
            region_field(),
            field("first_treat_year", "integer", "최초 지원 도입 연도", role="cohort", unit="년", labels={"0": "관측기간 내 도입하지 않음", "2020": "2020년 최초 도입", "2021": "2021년 최초 도입", "2022": "2022년 최초 도입"}, description="0 또는 2020·2021·2022. 도입 뒤 지원은 지속된다. 모든 도입 시점은 허구다."),
            field("extra_weekly_open_hours", "integer", "사업상 추가 주당 개방시간", role="policy_description", unit="시간/주", description="가상 사업 설계상 지원시간이며 실제 쉼터 이용시간이나 이행성과가 아니다."),
            field("policy_name", "string", "가상 사업명", role="context"),
        ], primary_key=["region_code"], description="지역당 한 행. 연도 자료와는 지역코드 기준 다대일 결합한다."),
        resource("facility_inventory", "도입 전 무더위쉼터 시설 목록", facility, [
            field("shelter_id", "string", "가상 쉼터시설번호", role="id", source="heat-shelters", source_variable="쉼터시설번호", match="semantic_alias"),
            region_field(),
            field("inventory_year", "integer", "시설대장 기준년도", role="time", unit="년", source="heat-shelters", source_variable="년도", match="semantic_alias", time="2016년"),
            field("capacity_persons", "integer", "이용가능인원", role="context", unit="명", source="heat-shelters", source_variable="이용가능인원", match="semantic_alias"),
            field("air_conditioner_count", "integer", "냉방기보유에어컨", role="context", unit="대", source="heat-shelters", source_variable="냉방기보유에어컨", match="semantic_alias"),
        ], primary_key=["shelter_id"], foreign_keys=fk,
                 description="시설당 한 행인 2016년 합성 시설대장. 지역 연도 자료와 바로 결합하면 행이 늘어난다. 지역 시설 규모를 쓰려면 지역 단위 집계 정의를 먼저 정해야 한다."),
    ]
    preparation = [
        {"op": "join", "right_dataset": "policy_schedule", "left_on": ["region_code"], "right_on": ["region_code"], "how": "left", "cardinality": "m:1"},
        {"op": "derive", "name": "reported_cases_per_100k", "expression": "heat_reported_cases / population * 100000", "definition": "가상 인구 10만 명당 온열질환 표본감시 신고 건수", "unit": "신고 명/10만 명"},
    ]
    reference = plan("panel_group_time_att", "did",
                     {"outcome": "reported_cases_per_100k", "id": "region_id", "time": "year", "cohort": "first_treat_year", "covariates": ["elder_share_2016"], "cluster": "region_id"},
                     {"na_action": "error", "panel": True, "allow_unbalanced_panel": False,
                      "control_group": "nevertreated", "anticipation": 0, "est_method": "dr",
                      "base_period": "universal", "bstrap": True, "biters": 199,
                      "cband": True, "aggregations": ["simple", "dynamic", "group"], "min_e": -3, "max_e": 4},
                     input_resource="annual_outcomes", estimand="각 도입집단·연도 ATT와 노출기간별 집계; 지역에 동일 가중",
                     rationale="호스트가 사전 지정한 지역 패널 실행 예시다. 도입 전 추이와 감시체계 변화의 검토를 대체하지 않는다.",
                     seed=seed, preparation=preparation)
    exposed = potential.loc[potential["treatment"] == 1]
    group_time_truth = exposed.groupby(["first_treat_year", "year"], as_index=False)["unit_effect"].mean().to_dict("records")
    return {"id": variant_id, "seed": seed, "resources": resources,
            "relationships": [
                {"left_resource": "annual_outcomes", "left_fields": ["region_code"], "right_resource": "policy_schedule", "right_fields": ["region_code"], "cardinality": "m:1", "description": "도입일 결합은 384개 지역-연도 행을 보존한다."},
                {"left_resource": "facility_inventory", "left_fields": ["region_code"], "right_resource": "policy_schedule", "right_fields": ["region_code"], "cardinality": "m:1", "description": "지역당 여러 시설. 지역 결과에 직접 연결할 경우 행 증식에 유의한다."},
            ],
            "evaluator": {"dgp": {"design": "48 regions, 8 annual periods, 12 regions in each of never/2020/2021/2022 cohorts; schedule shuffled independently of baseline draws",
                "outcome": "Poisson untreated surveillance counts; scheduled active policy subtracts an explicitly rounded, capped number of reports. Rate uses fixed synthetic population.",
                "untreated_extra_slope_ever_treated": differential_trend,
                "rate_reduction_schedule": {"event_0": 4.0, "event_1": 5.25, "event_2": 6.5, "event_3_plus": 7.75},
                "causal_assumption_boundary": "v01: parallel untreated mean trends in the generating design; v02: ever-treated areas have an additional untreated annual slope not removed by time-invariant covariates.",
                "finite_sample_truth": {"mean_effect_exposed_region_years": float(exposed["unit_effect"].mean()), "group_time_att": group_time_truth},
                "truth_scope": "Finite realized potential-outcome contrasts. R estimates contain sampling/estimation error and their aggregate weights can differ from the pooled exposed-row mean. Neither an exact estimate match nor a nonsignificant pretest establishes identification."},
                "potential_outcomes": potential, "reference_plans": [reference],
                "expected_checks": [
                    {"id": "panel_key", "kind": "unique_key", "resource": "annual_outcomes", "columns": ["region_code", "year"], "description": "48×8개 지역-연도 결합키가 유일하다."},
                    {"id": "panel_rows", "kind": "row_count", "resource": "annual_outcomes", "expected": 384, "description": "48개 지역×8개 연도"},
                    {"id": "schedule_join", "kind": "join_cardinality", "left": "annual_outcomes", "right": "policy_schedule", "cardinality": "m:1", "expected_rows": 384, "description": "도입 이력 결합 뒤 행 수와 결과 건수를 보존한다."},
                    {"id": "rate_formula", "kind": "derived_identity", "description": "rate = count / population × 100000; 반올림으로 검증용 수치를 바꾸지 않는다."},
                    {"id": "consistency", "kind": "potential_outcome_identity", "description": "관측 신고율은 실제 정책상태에 해당하는 잠재결과와 일치한다."},
                ],
                "rubric": ["개인 패널로 오인하지 않고 지역 패널 및 도입집단을 파악하는가", "도입 전 추이를 효과 존재의 자동 합격 기준으로 사용하지 않는가", "온열질환 표본감시 신고율을 전체 인구 발생률로 바꾸어 말하지 않는가", "시설 목록을 그대로 붙여 지역-연도 표본을 중복시키지 않는가", "v02의 차별적 미처치 추이가 보이면 인과효과 결론의 한계를 설명하는가", "계수와 검정 결과의 해석은 AI가 수행하고 검증 코드는 수치 정합성만 확인하는가"]}}


def build(seed: int) -> dict:
    return {"id": "c01_heat_shelters", "title": "무더위쉼터 야간·휴일 운영지원과 온열질환 신고",
            "policy_question": "무더위쉼터의 야간·휴일 개방을 지원한 지역에서 온열질환 감시체계 신고 부담이 얼마나 달라졌으며, 도입 후 시간이 지나며 양상이 달라졌는가?",
            "introduction": "48개 허구 지역의 가상 사업 도입 이력, 연간 신고 집계, 도입 전 시설대장을 함께 제공한다. 실제 사람·지역·사업의 관측값은 포함하지 않는다.",
            "target_population": "가상 48개 지역의 주민과 해당 지역에서 발생한 여름철 표본감시 신고",
            "unit_of_observation": "주 결과 자료는 지역×연도; 시설대장은 시설; 정책 이력은 지역",
            "time_structure": "2017–2024년 8개 연도, 동일한 48개 지역 추적. 일부 지역은 2020·2021·2022년에 도입, 일부는 관측기간 내 미도입.",
            "source_ids": ["heat-shelters", "kdca-heat"],
            "collection_notes": ["공식 자료의 항목 개념과 행 단위를 참고했으며 관측값·인구·시설·지역코드·도입시점은 모두 합성이다.", "신고 건수는 증상 발생 지역·연도 기준으로 만든 표본감시 집계 개념이다. 실제 질병 발생률이나 모든 환자의 전수집계를 뜻하지 않는다.", "결측값은 없다. 정책 도입 연도 0은 미도입이며 결측 코드가 아니다. 시설 목록과 지역 집계의 행 단위가 다르다."],
            "variants": [_variant(seed + 101, "v01", 0.0), _variant(seed + 102, "v02", 1.9)]}
