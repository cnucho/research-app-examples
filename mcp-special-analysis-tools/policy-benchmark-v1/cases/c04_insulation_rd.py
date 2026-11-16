"""Synthetic insulation-grant applications; all design choices are explicit.

The two variants differ in the administrative programs attached to the same
eligibility threshold. No real household, actual eligibility score, or tariff
is reproduced. Evaluator information is never included in a user resource.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from fixturelib import field, plan, resource


def _join(right: str) -> dict:
    return {"op": "join", "right_dataset": right,
            "left_on": ["application_id"], "right_on": ["application_id"],
            "how": "left", "cardinality": "1:1", "match_nulls": False,
            "suffixes": ["_left", "_right"], "max_output_rows": 1200}


def build(seed: int) -> dict:
    variants = []
    for number in (1, 2):
        variant_seed = int(seed) + 4000 + number
        rng = np.random.default_rng(variant_seed)
        n = 1200
        ids = [f"SYN-H{index:05d}" for index in range(1, n + 1)]
        score = np.round(rng.uniform(20, 100, n) * 2) / 2
        granted = (score >= 60).astype(int)
        appliance = granted.copy() if number == 2 else np.zeros(n, dtype=int)
        floor_area = np.round(rng.uniform(28, 110, n), 1)
        household_size = rng.integers(1, 6, n)
        built_year = rng.integers(1975, 2018, n)
        income = np.round(rng.uniform(90, 450, n), 1)
        z = score - 60
        baseline_mean = (320 + 1.3 * z + .014 * z ** 2
                         + .45 * (floor_area - 65) + 7 * (household_size - 3)
                         - .35 * (built_year - 1995))
        baseline_kwh = baseline_mean + rng.normal(0, 22, n)
        y00 = baseline_mean - 8 + rng.normal(0, 22, n)
        insulation_effect = -38.0
        appliance_effect = -18.0
        y10 = y00 + insulation_effect
        y01 = y00 + appliance_effect
        y11 = y00 + insulation_effect + appliance_effect
        observed = y00 + insulation_effect * granted + appliance_effect * appliance
        # A declared synthetic common tariff keeps the cost identity auditable.
        fixed_charge, unit_price = 1800, 230
        baseline_bill = np.rint(fixed_charge + unit_price * baseline_kwh).astype(int)
        followup_bill = np.rint(fixed_charge + unit_price * observed).astype(int)

        applications = pd.DataFrame({
            "application_id": ids, "need_score": score,
            "floor_area_m2": floor_area, "household_size": household_size,
            "building_year": built_year, "monthly_income_10kkrw": income,
            "application_date": ["2026-02-01"] * n,
        })
        awards = pd.DataFrame({
            "application_id": ids, "insulation_grant": granted,
            "appliance_grant": appliance, "program_start_date": ["2026-04-01"] * n,
        })
        bills = pd.DataFrame({
            "application_id": ids, "baseline_kwh": baseline_kwh,
            "followup_kwh": observed, "baseline_bill_krw": baseline_bill,
            "followup_bill_krw": followup_bill,
            "observation_days": np.full(n, 30, dtype=int),
        })
        rules = pd.DataFrame([
            {"policy_id": "SYN-INSULATION", "active": 1, "cutoff_score": 60.0,
             "eligibility_rule": "need_score >= 60", "start_date": "2026-04-01",
             "description": "가상 단열보강 현물지원; 기준을 충족한 모든 신청가구에 제공"},
            {"policy_id": "SYN-APPLIANCE", "active": int(number == 2), "cutoff_score": 60.0,
             "eligibility_rule": "active == 1 and need_score >= 60", "start_date": "2026-04-01",
             "description": "가상 고효율 냉방기기 교체지원; 시행 여부와 수급 여부는 행정기록 참조"},
        ])
        id_field = lambda: field("application_id", "string", "가상 신청가구 번호", role="identifier")
        resources = [
            resource("applications", "단열지원 신청 및 주택 현황", applications, [
                id_field(),
                field("need_score", "number", "지원 필요도 심사점수", unit="점",
                      description="이 사례를 위해 만든 20~100점 심사척도. 0.5점 단위이며 높을수록 지원 필요도가 높다. 실제 사업 심사기준이 아니다."),
                field("floor_area_m2", "number", "주거용 전용면적", unit="m2", source="housing-energy", source_variable="주거용 전용면적", match="concept_adaptation",
                      description="공식 가정부문 에너지조사의 주택면적 개념을 참고한 가상 항목. 원자료 변수코드를 복제하지 않았다."),
                field("household_size", "integer", "동거 가구원 수", unit="명", source="housing-energy", source_variable="가구원 수", match="concept_adaptation"),
                field("building_year", "integer", "주택 준공연도", source="housing-energy", source_variable="준공년도", match="concept_adaptation"),
                field("monthly_income_10kkrw", "number", "지원 전 가구 월소득", unit="만원", source="housing-energy", source_variable="월평균 가구원 소득", match="concept_adaptation", time="지원 이전",
                      description="공식 가정부문 조사의 소득 개념을 참고해 가구 전체 월소득으로 자체 정의한 가상 항목이다. 원자료 변수와 단위코드를 복제하지 않았다."),
                field("application_date", "string", "신청기준일", time="지원 이전"),
            ], primary_key=["application_id"]),
            resource("awards", "사업별 수급 행정기록", awards, [
                id_field(),
                field("insulation_grant", "integer", "단열지원 수급", labels={0: "미수급", 1: "수급"}),
                field("appliance_grant", "integer", "냉방기기 교체지원 수급", labels={0: "미수급", 1: "수급"}),
                field("program_start_date", "string", "공통 사업개시일", description="사업개시 기준일. 미수급 가구의 개별 설치일을 뜻하지 않는다."),
            ], primary_key=["application_id"], foreign_keys=[{"fields": ["application_id"], "reference": {"resource": "applications", "fields": ["application_id"]}}]),
            resource("bills", "동일 길이 관측기간 전력량과 청구액", bills, [
                id_field(),
                field("baseline_kwh", "number", "지원 전 30일 전력사용량", unit="kWh", time="2025년 동월 30일"),
                field("followup_kwh", "number", "지원 후 30일 전력사용량", unit="kWh", time="2026년 동월 30일"),
                field("baseline_bill_krw", "integer", "지원 전 가상 전기청구액", unit="원", description="round(1800 + 230 × baseline_kwh). 실제 전기요금제와 다르다."),
                field("followup_bill_krw", "integer", "지원 후 가상 전기청구액", unit="원", description="round(1800 + 230 × followup_kwh). 실제 전기요금제와 다르다."),
                field("observation_days", "integer", "각 청구자료의 관측기간", unit="일", description="모든 가구의 전후 관측기간은 각각 30일이다."),
            ], primary_key=["application_id"], foreign_keys=[{"fields": ["application_id"], "reference": {"resource": "applications", "fields": ["application_id"]}}]),
            resource("policy_rules", "가상 사업의 공개 운영규칙", rules, [
                field("policy_id", "string", "가상 사업번호", role="identifier"),
                field("active", "integer", "사업 시행 여부", labels={0: "미시행", 1: "시행"}),
                field("cutoff_score", "number", "지원기준 점수", unit="점"),
                field("eligibility_rule", "string", "공개 수급조건"),
                field("start_date", "string", "사업 시작일"),
                field("description", "string", "사업 내용"),
            ], primary_key=["policy_id"]),
        ]
        preparation = [_join("awards"), _join("bills")]
        reference = plan(
            "rd_kwh_cutoff", "rd",
            {"outcome": "followup_kwh", "running": "need_score", "covariates": ["baseline_kwh", "floor_area_m2"], "id": "application_id"},
            {"na_action": "error", "cutoff": 60, "p": 1, "q": 2,
             "kernel": "triangular", "vce": "hc3", "masspoints": "adjust",
             "bandwidth_method": "mserd", "plot_bins": [12, 12], "plot_covariate_evaluation": "mean"},
            input_resource="applications", preparation=preparation, seed=variant_seed,
            estimand="need_score=60에서 우측(수급기준 충족)과 좌측의 국소 전력사용량 불연속, kWh",
            rationale="호스트가 명시한 sharp RD 계산. v02에서는 동일 기준의 두 지원이 함께 바뀌므로 이 계산만으로 단열지원의 단독 효과를 분리할 수 없다.")
        variants.append({
            "id": f"v{number:02d}", "seed": variant_seed,
            "resources": resources,
            "relationships": [{"left_resource": "applications", "right_resource": right,
                               "left_fields": ["application_id"], "right_fields": ["application_id"],
                               "cardinality": "1:1", "expected_matched_rows": n, "expected_unmatched_left": 0,
                               "description": "신청가구 1,200개 ID를 보존하는 일대일 결합이다. 공개 운영규칙은 정책별 자료이며 가구행에 직접 결합하지 않는다."}
                              for right in ("awards", "bills")],
            "evaluator": {
                "dgp": {"assignment": "insulation=1[need_score>=60]", "score_distribution": "Uniform(20,100), rounded to nearest 0.5",
                        "mean_no_support": "320+1.3*z+0.014*z^2+0.45*(floor_area-65)+7*(household_size-3)-0.35*(building_year-1995)-8; z=need_score-60",
                        "followup_error": "Normal(0,22^2)", "insulation_effect_kwh": insulation_effect,
                        "appliance_effect_kwh": appliance_effect, "appliance_policy_active": number == 2,
                        "observed_cutoff_jump_kwh": insulation_effect + (appliance_effect if number == 2 else 0),
                        "target_definitions": {"policy_specific_effect": "Y(1,a)-Y(0,a)=-38 for fixed appliance status a",
                                               "observed_threshold_estimand": "Y(1,active)-Y(0,0)"},
                        "measurement": "No outcome clipping or minimum-p-value seed selection. Electricity tariffs and policy rules are fictional."},
                "potential_outcomes": pd.DataFrame({"application_id": ids, "y_no_support_kwh": y00,
                    "y_insulation_only_kwh": y10, "y_appliance_only_kwh": y01,
                    "y_both_kwh": y11, "observed_followup_kwh": observed,
                    "insulation_effect_kwh": np.full(n, insulation_effect)}),
                "reference_plans": [reference],
                "expected_checks": [
                    {"id": "join_rows", "kind": "exact_structural", "description": "각 신청 ID는 수급·청구자료와 1:1로 결합된다.", "expected_rows": n, "expected_unmatched": 0},
                    {"id": "sharp_assignment", "kind": "exact_arithmetic", "description": "insulation_grant == int(need_score >= 60)"},
                    {"id": "billing_identity", "kind": "exact_arithmetic", "description": "followup_bill_krw == round(1800 + 230 * followup_kwh)"},
                    {"id": "package_parity", "kind": "numerical_reference", "description": "동일 h/b 선택과 옵션을 사용하는 rdrobust 직접 실행과 비교한다. 생성효과와 단일 추정치를 동일시하지 않는다."},
                    {"id": "cutoff_policy_review", "kind": "host_review", "description": "공개 사업규칙과 각 수급변수를 대조해 국소 불연속에 함께 포함되는 정책을 설명한다."},
                ],
                "rubric": ["지원 방향은 점수 60 이상이다. 결과의 우측-좌측 부호를 뒤집지 않는다.",
                           "점수의 0.5점 단위를 설명하고 masspoints 옵션과 실제 대역폭을 드러낸다.",
                           "현재 엔진이 밀도조작 검정을 실행했다고 주장하지 않는다.",
                           "v02의 동시 시행 지원을 무시하거나 완전 공선인 수급변수를 통제해 단독 인과효과를 식별했다고 주장하면 안 된다.",
                           "정책효과의 평가대상을 기준점 부근 신청가구로 제한하고 전체 가구로 무조건 일반화하지 않는다."],
            },
        })
    return {
        "id": "c04_home_insulation", "title": "주거 단열지원 기준과 전력소비",
        "policy_question": "주거환경 개선지원이 기준점 부근 신청가구의 전력사용량과 부담에 어떤 차이를 만들었는가?",
        "introduction": "가상 지자체의 단열지원 신청, 사업 운영규칙, 수급기록, 전후 전력청구자료를 결합한다. 실제 사업의 심사점수나 요금체계를 재현한 자료가 아니다.",
        "target_population": "가상 지자체의 주거환경 개선지원 신청 1,200가구", "unit_of_observation": "신청가구",
        "time_structure": "지원 전후 각각 동일한 30일 관측창; 신청점수와 공개 사업기준 포함",
        "source_ids": ["housing-energy"],
        "collection_notes": ["가구번호는 완전 가상 문자열이다. 실제 가구나 주소는 포함하지 않는다.",
                             "주택면적·가구원 수·준공연도·월소득은 공식 에너지조사의 개념을 참고해 자체 정의했으며 원자료 변수코드가 아니다.",
                             "공개 운영규칙과 개별 사업 수급자료를 함께 제공한다. 분석계획과 해석은 호스트 AI가 작성한다."],
        "variants": variants,
    }
