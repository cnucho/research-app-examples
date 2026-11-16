"""Independent repeated cross sections for a fictional youth transport policy."""
from __future__ import annotations

import numpy as np
import pandas as pd

from fixturelib import field, logistic, plan, resource


def _variant(seed: int, variant_id: str, composition_change: bool) -> dict:
    rng = np.random.default_rng(seed)
    periods = [20211, 20212, 20221, 20222]
    cohorts = np.repeat([0, 20221], 20)
    rng.shuffle(cohorts)
    region_effect = rng.normal(0, 9, 40)
    rows, schedules, potentials = [], [], []
    target_degree_share = .45
    for region_id in range(1, 41):
        cohort = int(cohorts[region_id - 1])
        schedules.append({"region_id": region_id, "sigun_code": f"{9000 + region_id:04d}",
                          "first_treat_period": cohort, "first_treat_wave": 3 if cohort else 0,
                          "monthly_support_krw": 100000 if cohort else 0})
        for t, period in enumerate(periods):
            active = int(cohort > 0 and period >= cohort)
            sampled_degree_share = .8 if composition_change and active else target_degree_share
            for person_id in range(1, 21):
                sex = int(rng.choice([1, 2]))
                degree = int(rng.random() < sampled_degree_share)
                age = int(rng.integers(23 if degree else 19, 35))
                u = rng.random()
                p0 = float(logistic(-.1 + .07 * (age - 25) + .55 * degree))
                e0 = int(u < p0)
                e1 = int(u < min(1., p0 + .08))
                wage_base = max(40., 165 + 3.5 * (age - 25) + 48 * degree
                                + 9 * (sex == 1) + region_effect[region_id - 1]
                                + 4 * t + rng.normal(0, 24))
                y0 = round(e0 * wage_base, 4)
                y1 = round(e1 * (wage_base + 22 + 8 * degree), 4)
                employment = e1 if active else e0
                observed = y1 if active else y0
                weight = (target_degree_share / sampled_degree_share if degree
                          else (1 - target_degree_share) / (1 - sampled_degree_share))
                rows.append({"region_id": region_id, "survey_period": period,
                             "wave_index": t + 1,
                             "sample_person_id": person_id, "survey_year": period // 10,
                             "survey_half": period % 10, "sex": sex, "age": age,
                             "college_completed_pre_policy": degree,
                             "employed": employment, "monthly_earnings_10kkrw": observed,
                             "survey_weight": float(weight)})
                potentials.append({"region_id": region_id, "survey_period": period,
                                   "wave_index": t + 1, "sample_person_id": person_id,
                                   "first_treat_period": cohort, "first_treat_wave": 3 if cohort else 0,
                                   "treatment": active, "y0": y0, "y1": y1,
                                   "unit_effect": y1 - y0, "observed": observed,
                                   "employment_y0": e0, "employment_y1": e1,
                                   "survey_weight": float(weight),
                                   "degree_sampling_probability": sampled_degree_share})
    data, schedule, potential = pd.DataFrame(rows), pd.DataFrame(schedules), pd.DataFrame(potentials)
    resources = [
        resource("survey_rows", "청년 경제활동 합성 반복횡단면 조사", data, [
            field("region_id", "integer", "가상 조사 지역번호", role="cluster", description="동일 지역번호가 여러 시점에 나와도 같은 사람을 재조사했다는 뜻은 아니다."),
            field("survey_period", "integer", "조사 연도·반기 결합코드", role="time", description="20211=2021년 상반기, 20212=하반기, 20221·20222도 같은 규칙이다. 날짜나 개인 ID가 아니다."),
            field("wave_index", "integer", "연속 반기 순번", role="time", unit="반기", description="1=2021년 상반기, 2=2021년 하반기, 3=2022년 상반기, 4=2022년 하반기. 반기 간 간격은 1이다. 연도·반기 표현코드의 숫자 차이를 경과시간으로 쓰지 않는다."),
            field("sample_person_id", "integer", "지역·조사시점 안의 응답번호", role="id", description="1–20을 각 지역·반기마다 새로 사용한다. 전체 고유키는 region_id+survey_period+sample_person_id이며 사람의 종단 식별자로 쓰면 안 된다."),
            field("survey_year", "integer", "조사년도", role="time", unit="년", source="kostat-employment", source_variable="조사년도", match="semantic_alias"),
            field("survey_half", "integer", "조사반기", role="time", labels={"1": "상반기·4월", "2": "하반기·10월"}, source="kostat-employment", source_variable="조사주기: 반기", match="semantic_alias"),
            field("sex", "integer", "성별", role="covariate", labels={"1": "남성", "2": "여성"}, source="kostat-employment", source_variable="성별", match="semantic_alias", description="성별 개념을 참고한 자체 코드. MDIS 원파일의 영문 변수명·값코드를 그대로 차용했다는 뜻이 아니다."),
            field("age", "integer", "조사 당시 만나이", role="covariate", unit="세", source="kostat-employment", source_variable="연령", match="semantic_alias", question="조사 기준일 현재 만 나이는 몇 세입니까?"),
            field("college_completed_pre_policy", "integer", "사업 도입 전 대학 졸업 여부", role="pre_treatment_covariate", labels={"0": "미졸업", "1": "졸업"}, description="사업 최초 도입 전인 2020년 말 기준 이력을 회고 확인한 자체 문항. 일반 조사 교육정도 항목과 완전히 같은 변수는 아니다.", question="2020년 말까지 전문대학 또는 대학을 졸업했습니까?", time="2020년 말"),
            field("employed", "integer", "조사 기준 취업 여부", role="context", labels={"0": "미취업", "1": "취업"}, source="kostat-employment", source_variable="수입 있는 일·무급가족 일·일시휴직", match="semantic_alias", description="교육용으로 취업 상태를 이분화한 합성 변수. 공식 경제활동 판정 알고리즘을 구현한 것이 아니다."),
            field("monthly_earnings_10kkrw", "number", "최근 3개월 평균 월 근로소득", role="outcome", unit="만원/월", description="전체 표본의 자체 정의 근로소득. 합성 미취업자는 0이고 취업자는 연속값이다. 임금근로자만의 평균임금과 모집단·분모가 다르다.", question="최근 3개월의 월평균 근로소득은 얼마입니까? 이 연습자료에서는 미취업을 0으로 정의합니다.", time="조사 전 최근 3개월"),
            field("survey_weight", "number", "가상 표집확률 비율 가중치", role="weight", description="알려진 합성 표집확률 q에 대해 대학졸업자는 0.45/q, 비졸업자는 0.55/(1-q)를 부여한 비율 가중치다. 기대적으로 공통 대학졸업 구성 0.45를 목표로 하며, 유한표본의 실제 비중을 정확히 0.45로 맞춘 사후층화가 아니다. 실제 통계청 가중치가 아니며 가중치만으로 복합표본 분산추정이 구현되는 것도 아니다."),
        ], primary_key=["region_id", "survey_period", "sample_person_id"],
                 foreign_keys=[{"fields": ["region_id"], "reference": {"resource": "policy_schedule", "fields": ["region_id"]}}],
                 description="40개 지역×4개 반기×20명=3200명. 각 행은 독립적으로 새로 조사한 응답자이며 개인은 추적하지 않는다. 결측은 없다. 미취업자의 소득 0은 결측과 다르다."),
        resource("policy_schedule", "가상 청년 교통·구직지원 지역 이력", schedule, [
            field("region_id", "integer", "가상 조사 지역번호", role="key"),
            field("sigun_code", "string", "가상 시군코드", role="id", source="kostat-employment", source_variable="시군코드(A·D형 4자리)", match="semantic_alias", description="4자리 표현을 참고한 허구 코드 9001–9040. 실제 시군을 식별하지 않으며 문자열로 보존한다."),
            field("first_treat_period", "integer", "최초 지원 반기", role="cohort", labels={"0": "관측기간 내 미도입", "20221": "2022년 상반기 도입"}, description="최초 도입 이후 계속 지원하는 허구 이력. 같은 지역의 모든 조사 행에 동일한 값으로 결합한다."),
            field("first_treat_wave", "integer", "최초 지원 반기의 연속 순번", role="cohort", unit="반기", labels={"0": "관측기간 내 미도입", "3": "2022년 상반기·세 번째 조사"}, description="wave_index와 같은 1–4 시간척도를 사용한다. first_treat_period=20221은 3, 미도입은 0에 대응한다."),
            field("monthly_support_krw", "integer", "가상 월 지원한도", role="policy_description", unit="원/월", description="사업 설계상의 한도이며 개인의 실제 수령액은 아니다."),
        ], primary_key=["region_id"], description="40개 지역별 한 행. 정책 수혜 여부는 지역 도입일과 조사시점으로 정의하는 지역 수준 노출이다."),
    ]
    preparation = [{"op": "join", "right_dataset": "policy_schedule", "left_on": ["region_id"], "right_on": ["region_id"], "how": "left", "cardinality": "m:1"}]
    common_options = {"na_action": "error", "panel": False, "control_group": "nevertreated",
                      "anticipation": 0, "est_method": "dr", "base_period": "universal",
                      "bstrap": True, "biters": 199, "cband": True,
                      "aggregations": ["simple", "dynamic"], "min_e": -2, "max_e": 1,
                      "factor_levels": {"sex": ["1", "2"]}}
    variables = {"outcome": "monthly_earnings_10kkrw", "time": "wave_index", "cohort": "first_treat_wave",
                 "covariates": ["age", "sex", "college_completed_pre_policy"], "cluster": "region_id", "weights": "survey_weight"}
    reference = plan("repeated_cross_section_att", "did", variables, common_options,
                     input_resource="survey_rows", estimand="공통 학력구성으로 보정한 지역정책 노출집단의 반기별 ATT",
                     rationale="새 응답자를 매 반기 조사하므로 호스트가 panel=false와 지역 군집을 명시한다. 합성 가중치는 표본구성 보정용이며 자체적인 인과 식별 근거가 아니다.",
                     seed=seed, preparation=preparation)
    exposed = potential.loc[potential["treatment"] == 1]
    return {"id": variant_id, "seed": seed, "resources": resources,
            "relationships": [{"left_resource": "survey_rows", "left_fields": ["region_id"], "right_resource": "policy_schedule", "right_fields": ["region_id"], "cardinality": "m:1", "description": "정책 이력 결합 뒤 3200개의 독립 조사 행이 보존된다."}],
            "evaluator": {"dgp": {"design": "40 regions; independent 20-person samples per region at each of 4 periods; 20 never-treated and 20 adopting in 20221",
                "population_degree_share": target_degree_share,
                "treated_post_sample_degree_share": .8 if composition_change else target_degree_share,
                "employment_probability_increment_under_treatment": .08,
                "earnings_increment_among_employed": "22 + 8 * college_completed_pre_policy in 10,000 KRW/month",
                "sampling_boundary": "v02 deliberately changes treated-post education composition. Weights correct this declared sampling component, not arbitrary unmeasured changes.",
                "untreated_trends": "Stable age/sex distribution and stable underlying degree mix; untreated earnings wage component has common +4 per half-year. Degree-dependent sample selection differs only in v02.",
                "conditional_parallel_trends": "At fixed age and degree, p0=logistic(-0.1+0.07*(age-25)+0.55*degree), so the untreated earnings conditional mean increment is 4*p0 per half-year. This conditional parallel-trend design is distinct from correct specification of a linear nuisance regression. The DR reference execution does not certify its nuisance models or identify effects from the user data alone.",
                "finite_sample_truth": {"unweighted_att_exposed_rows": float(exposed["unit_effect"].mean()), "weighted_att_exposed_rows": float(np.average(exposed["unit_effect"], weights=exposed["survey_weight"]))},
                "truth_scope": "Potential outcomes exist per sampled person. These are finite sampled-unit contrasts; they are not the package estimate, a population theorem, or proof that pretrends pass."},
                "potential_outcomes": potential, "reference_plans": [reference],
                "expected_checks": [
                    {"id": "survey_key", "kind": "unique_key", "resource": "survey_rows", "columns": ["region_id", "survey_period", "sample_person_id"], "description": "지역·반기·응답번호의 결합키가 유일하다."},
                    {"id": "fresh_people", "kind": "design_metadata", "description": "반복되는 응답번호는 독립 응답자의 지역·시점 내 번호이다. 패널로 연결하지 않는다."},
                    {"id": "survey_rows", "kind": "row_count", "resource": "survey_rows", "expected": 3200, "description": "40×4×20 조사 행"},
                    {"id": "weight_positive", "kind": "numeric_domain", "resource": "survey_rows", "column": "survey_weight", "minimum_exclusive": 0, "description": "모든 합성 가중치는 양수이며 도입시점 결합과 무관하게 보존된다."},
                    {"id": "schedule_join", "kind": "join_cardinality", "cardinality": "m:1", "expected_rows": 3200, "description": "40행 정책 이력으로 결합하되 사람 수가 증식하지 않는다."},
                    {"id": "zero_is_not_missing", "kind": "domain_identity", "description": "미취업자의 근로소득 0을 임금 결측이나 분석 제외로 바꾸지 않는다."},
                ],
                "rubric": ["지역·시점별 독립 표본이므로 반복횡단면으로 이해하는가", "응답번호 재사용을 동일인 추적의 근거로 삼지 않는가", "전체 청년의 소득과 취업자 평균임금의 질문 차이를 설명하는가", "표본구성·가중치와 결과 변화의 관계를 AI가 검토하는가", "가중치 사용을 복합표본설계 전체 지원과 혼동하지 않는가", "비관측 구성 변화가 남을 수 있음을 과장 없이 설명하는가"]}}


def build(seed: int) -> dict:
    return {"id": "c02_youth_transport", "title": "청년 교통·구직지원과 지역 청년의 월 근로소득",
            "policy_question": "구직 교통비를 지원한 지역에서 만 19–34세 청년 전체의 월 근로소득이 달라졌는가? 반기마다 조사한 사람이 다른 자료로 어떤 범위의 답을 할 수 있는가?",
            "introduction": "지역별고용조사의 반기 조사·경제활동 항목·메타자료 관행을 참고한 독립 합성조사다. 특정 실제 정책이나 MDIS 원자료의 재현이 아니다.",
            "target_population": "40개 허구 지역의 각 조사시점 만 19–34세 청년",
            "unit_of_observation": "해당 지역·반기에 새로 뽑은 개인; 정책 도입 이력은 지역",
            "time_structure": "2021년 상·하반기와 2022년 상·하반기. 매 시점 독립 표본이며 개인 종단 연결이 없다.",
            "source_ids": ["kostat-employment"],
            "collection_notes": ["40개 지역에서 반기마다 20명을 새로 조사한 설정이다. 표본번호 1–20은 각 지역·반기에서 재사용한다.", "최초 도입 반기는 20221 또는 0이다. 정책 이력은 지역번호로 다대일 결합한다.", "표본의 학력구성과 합성 보정가중치를 함께 제공한다. 실제 조사 가중치·원래 MDIS 필드명·실제 값코드와 같다는 주장은 하지 않는다.", "전체 청년을 분모로 한 근로소득을 자체 정의했다. 미취업 0을 포함하므로 임금근로자만의 평균임금과 다르다. 결측값은 없다."],
            "variants": [_variant(seed + 201, "v01", False), _variant(seed + 202, "v02", True)]}
