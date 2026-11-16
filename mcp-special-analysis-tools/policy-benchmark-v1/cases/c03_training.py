"""Observational training support with explicit ANCOVA and matching plans."""
from __future__ import annotations

import numpy as np
import pandas as pd

from fixturelib import field, logistic, plan, resource


def _variant(seed: int, variant_id: str, limited_overlap: bool) -> dict:
    rng = np.random.default_rng(seed)
    n = 900
    ids = [f"TR{i:05d}" for i in range(1, n + 1)]
    sex = rng.choice([1, 2], n)
    age = rng.integers(20, 55, n)
    education = rng.choice([9, 12, 14, 16, 18], n, p=[.08, .35, .23, .29, .05])
    education = np.minimum(education, np.where(age < 22, 14, np.where(age < 24, 16, 18)))
    baseline_employed = (rng.random(n) < logistic(.35 + .035 * (age - 35) + .15 * (education - 12))).astype(int)
    baseline_earnings = np.round(baseline_employed * np.maximum(20, 150 + 1.9 * (age - 30) + 8 * (education - 12) + 12 * (sex == 1) + rng.normal(0, 38, n)), 4)
    experience = rng.choice([1, 2, 3, -1], n, p=[.22, .04, .71, .03])
    if limited_overlap:
        log_odds = 1.3 * (education - 14) + .05 * (baseline_earnings - 170) + .06 * (age - 35)
    else:
        log_odds = -.15 + .16 * (education - 14) - .0025 * (baseline_earnings - 150) + .016 * (age - 35) + .25 * (sex == 2)
    propensity = logistic(log_odds)
    treatment = (rng.random(n) < propensity).astype(int)
    employment_uniform = rng.random(n)
    p_employed0 = logistic(.1 + .008 * baseline_earnings + .12 * (education - 12) - .012 * (age - 35))
    e0 = (employment_uniform < p_employed0).astype(int)
    e1 = (employment_uniform < np.minimum(1., p_employed0 + .09)).astype(int)
    wage0 = np.maximum(20, 135 + .45 * baseline_earnings + 1.25 * (age - 35) + 7 * (education - 12) + 8 * (sex == 1) + rng.normal(0, 32, n))
    wage_gain = 30 + 6 * (education <= 12) + 4 * (sex == 2)
    y0 = np.round(e0 * wage0, 4)
    y1 = np.round(e1 * (wage0 + wage_gain), 4)
    y = np.where(treatment == 1, y1, y0)
    followed_employed = np.where(treatment == 1, e1, e0)
    hours = np.where(treatment == 1, rng.choice([120, 160, 200], n, p=[.2, .6, .2]), 0)
    completed = np.where(treatment == 1, (rng.random(n) < .88).astype(int), 0)
    baseline = pd.DataFrame({"person_id": ids, "sex": sex, "age": age,
                             "education_years": education, "baseline_employed": baseline_employed,
                             "baseline_earnings_10kkrw": baseline_earnings,
                             "prior_training_experience": experience})
    register = pd.DataFrame({"person_id": ids, "program_participation": treatment,
                            "training_hours": hours, "training_completed": completed})
    followup = pd.DataFrame({"person_id": ids, "followup_months": np.full(n, 6),
                            "followup_employed": followed_employed,
                            "followup_earnings_10kkrw": y})
    potential = pd.DataFrame({"person_id": ids, "treatment": treatment,
                             "y0": y0, "y1": y1, "unit_effect": y1 - y0,
                             "observed": y, "assignment_probability": propensity,
                             "employment_y0": e0, "employment_y1": e1})
    person_field = lambda: field("person_id", "string", "합성 개인고유번호", role="id", source="klips", source_variable="pid", match="semantic_alias", description="TR로 시작하는 자체 합성 ID. 실제 KLIPS 개인번호와 연결할 수 없다.")
    resources = [
        resource("baseline", "참여 이전 기초조사", baseline, [
            person_field(),
            field("sex", "integer", "성별", role="pre_treatment_covariate", labels={"1": "남자", "2": "여자"}, source="klips", source_variable="p__0101", match="semantic_alias", question="성별을 선택해 주십시오.", time="사업 참여 이전"),
            field("age", "integer", "만나이", role="pre_treatment_covariate", unit="세", source="klips", source_variable="p__0107", match="semantic_alias", question="사업 시작일 기준 만 나이는 몇 세입니까?", time="사업 참여 이전"),
            field("education_years", "integer", "완료한 정규교육 연수", role="pre_treatment_covariate", unit="년", description="9·12·14·16·18년의 자체 합성 교육연수. KLIPS p__0110의 학교 구분 원래 코드와 같지 않다.", question="사업 이전에 완료한 정규교육 기간은 몇 년입니까?", time="사업 참여 이전"),
            field("baseline_employed", "integer", "기초시점 취업 여부", role="pre_treatment_covariate", labels={"0": "미취업", "1": "취업"}, description="가상 사업의 자체 이분형 지표. KLIPS 취업자/미취업자 설문 구분 코드와 구별한다.", time="사업 참여 이전"),
            field("baseline_earnings_10kkrw", "number", "참여 전 월 근로소득", role="pre_treatment_covariate", unit="만원/월", description="전체 대상자에 대한 자체 정의 소득. 미취업이면 0이며 결측이 아니다. KLIPS p__1642의 임금근로자 월평균임금과 분모가 다르다.", question="사업 이전 기준월의 총 근로소득은 얼마입니까? 미취업은 0으로 기록합니다.", time="사업 시작 전 기준월"),
            field("prior_training_experience", "integer", "기초시점 직업훈련 경험", role="context", labels={"1": "받은 경험 있음", "2": "현재 받는 중", "3": "받은 적 없음", "-1": "모름/무응답"}, missing=[-1], source="klips", source_variable="p__4501", match="semantic_alias", description="일반 직업훈련 경험을 나타낸다. 이 가상 사업 참여변수와 같지 않다. -1은 KLIPS 통합코드북의 모름/무응답 개념을 참고했다.", time="가상 사업 참여 이전"),
        ], primary_key=["person_id"], description="900명 기초조사. prior_training_experience에만 -1 무응답이 존재한다. 나머지 분석 입력은 완전 관측되었다는 연습 설정이다."),
        resource("program_register", "가상 디지털 재취업교육 사업명부", register, [
            person_field(),
            field("program_participation", "integer", "가상 사업 참여", role="treatment", labels={"0": "비참여", "1": "참여"}, description="특정 허구 사업의 참여 여부. KLIPS p__4501 일반 훈련경험 변수를 재코딩한 것이 아니다. 무작위 배정 기록은 없다."),
            field("training_hours", "integer", "사업 내 수강시간", role="post_treatment_measure", unit="시간", description="참여 후 측정한 이행정보. 비참여자는 0이다. 기초 공변량으로 간주하지 않는다."),
            field("training_completed", "integer", "사업 이수 여부", role="post_treatment_measure", labels={"0": "미이수 또는 비참여", "1": "이수"}, description="참여 뒤의 이행정보. 비참여자와 미이수 참여자 구별은 program_participation과 함께 해야 한다."),
        ], primary_key=["person_id"], foreign_keys=[{"fields": ["person_id"], "reference": {"resource": "baseline", "fields": ["person_id"]}}],
                 description="기초 대상자와 동일한 900명의 참여명부. 비참여자도 한 행을 가진다."),
        resource("followup_6m", "사업 기준일 6개월 뒤 추적조사", followup, [
            person_field(),
            field("followup_months", "integer", "추적 간격", role="time", unit="개월", description="참여자·비참여자 모두 공통 사업 기준일로부터 6개월이다."),
            field("followup_employed", "integer", "6개월 뒤 취업 여부", role="secondary_outcome", labels={"0": "미취업", "1": "취업"}, time="공통 기준일 6개월 뒤"),
            field("followup_earnings_10kkrw", "number", "6개월 뒤 월 근로소득", role="outcome", unit="만원/월", description="전체 대상자의 자체 정의 월 근로소득. 미취업 0을 포함한다. KLIPS 임금근로자용 p__1642를 동일 의미로 복제한 변수가 아니다.", question="추적 기준월의 월 근로소득은 얼마입니까? 미취업은 0으로 기록합니다.", time="공통 기준일 6개월 뒤"),
        ], primary_key=["person_id"], foreign_keys=[{"fields": ["person_id"], "reference": {"resource": "baseline", "fields": ["person_id"]}}],
                 description="이 기본 패키지는 900명 모두 추적 성공한 설정이다. 실제 사업에서 흔한 추적탈락을 해결했다고 주장하지 않는다."),
    ]
    prep = [
        {"op": "join", "right_dataset": "program_register", "left_on": ["person_id"], "right_on": ["person_id"], "how": "left", "cardinality": "1:1"},
        {"op": "join", "right_dataset": "followup_6m", "left_on": ["person_id"], "right_on": ["person_id"], "how": "left", "cardinality": "1:1"},
    ]
    covariates = ["sex", "age", "education_years", "baseline_employed", "baseline_earnings_10kkrw"]
    ancova = plan("adjusted_group_difference", "ancova",
                  {"outcome": "followup_earnings_10kkrw", "group": "program_participation", "covariates": covariates, "id": "person_id"},
                  {"na_action": "error", "group_levels": ["0", "1"], "se_type": "HC3",
                   "reference_distribution": "t", "df_method": "residual", "adjustment": "empirical",
                   "standardization_weights": "equal", "contrasts": [{"id": "participation_1_minus_0", "numerator": "1", "denominator": "0"}],
                   "p_adjust": "none", "group_interactions": [], "factor_levels": {"sex": ["1", "2"]}},
                  input_resource="baseline", estimand="분석 표본의 기초 공변량 분포에서 표준화한 참여·비참여 집단의 조정 평균차",
                  rationale="호스트가 지정한 관측자료 ANCOVA 실행 예시. 선형 공변량 조정으로 모든 선택편의를 제거했다고 주장하지 않는다.", seed=seed, preparation=prep)
    matching = plan("one_to_one_matching_att", "matching",
                    {"outcome": "followup_earnings_10kkrw", "treatment": "program_participation", "covariates": covariates, "id": "person_id"},
                    {"na_action": "error", "method": "nearest", "distance": "glm", "link": "logit",
                     "estimand": "ATT", "replace": False, "ratio": 1, "caliper": .2, "std_caliper": True,
                     "m_order": "largest", "effect_estimator": "paired_mean", "outcome_type": "continuous",
                     "balance_s_d_denom": "treated", "balance_binary": "std", "factor_levels": {"sex": ["1", "2"]}},
                    input_resource="baseline", estimand="명시한 매칭 규칙으로 유지된 참여자의 대응쌍 평균차; 전체 참여자 ATT와 구별",
                    rationale="호스트가 지정한 1:1 비복원 최근접 성향점수 매칭. 중첩·탈락·균형과 매칭 표본의 대상 변화를 별도로 검토한다.", seed=seed, preparation=prep)
    treated = potential.loc[potential["treatment"] == 1]
    return {"id": variant_id, "seed": seed, "resources": resources,
            "relationships": [
                {"left_resource": "baseline", "left_fields": ["person_id"], "right_resource": "program_register", "right_fields": ["person_id"], "cardinality": "1:1", "description": "같은 대상자 명부를 개인고유번호로 결합한다."},
                {"left_resource": "baseline", "left_fields": ["person_id"], "right_resource": "followup_6m", "right_fields": ["person_id"], "cardinality": "1:1", "description": "동일한 900명 모두 추적조사한 기본 설정이다."},
            ],
            "evaluator": {"dgp": {"design": "900 observational participants and nonparticipants; treatment sampled from an explicit logistic function of measured baseline variables",
                "oracle_link": {"observed_id": "person_id", "oracle_id": "person_id", "effect_column": "unit_effect"},
                "assignment_logit": "1.3*(education_years-14)+.05*(baseline_earnings-170)+.06*(age-35)" if limited_overlap else "-.15+.16*(education_years-14)-.0025*(baseline_earnings-150)+.016*(age-35)+.25*(sex==2)",
                "assignment_probability_range": [float(propensity.min()), float(propensity.max())],
                "employment_probability_increment": .09,
                "employed_wage_gain": "30+6*(education_years<=12)+4*(sex==2) in 10,000 KRW/month",
                "ignorability_scope": "In this authored generator, assignment uses observed baseline variables and a random draw independent of outcome noise. The user-facing observational data alone cannot establish this assumption.",
                "overlap_boundary": "v02 has intentionally steep selection and limited common support; changing algorithms does not create absent counterfactual support.",
                "finite_sample_truth": {"ate_all_900": float(potential["unit_effect"].mean()), "att_all_observed_participants": float(treated["unit_effect"].mean()), "participant_n": int(treatment.sum())},
                "truth_scope": "True contrasts are finite-sample potential-outcome means. The matched estimand requires the actual retained treated IDs; its truth must be recomputed for those IDs. An ANCOVA contrast, population coefficient and retained-sample ATT are not interchangeable."},
                "potential_outcomes": potential, "reference_plans": [ancova, matching],
                "expected_checks": [
                    {"id": "baseline_key", "kind": "unique_key", "resource": "baseline", "columns": ["person_id"], "description": "모든 원자료에서 개인키가 한 번씩만 나타난다."},
                    {"id": "baseline_n", "kind": "row_count", "resource": "baseline", "expected": 900, "description": "기초 표본 900명"},
                    {"id": "one_to_one_join", "kind": "join_cardinality", "cardinality": "1:1", "expected_rows": 900, "description": "명부와 추적조사를 결합해도 900명이며 결과 합계가 보존된다."},
                    {"id": "missing_semantics", "kind": "declared_missing", "resource": "baseline", "column": "prior_training_experience", "values": [-1], "description": "일반 훈련경험의 -1은 무응답이며 참여·소득의 0과 다르다. 참조 분석은 이 변수를 사용하지 않는다."},
                    {"id": "pre_only", "kind": "plan_contract", "description": "성향점수·기초 공변량 조정에 수강시간·이수·추적 취업 여부를 넣지 않는다."},
                    {"id": "matched_truth", "kind": "retained_sample_truth", "description": "실제 유지된 참여자 ID의 unit_effect 평균만 해당 매칭 표본 진실값이다. 추정치와 정확히 같은지를 합격조건으로 삼지 않는다."},
                ],
                "rubric": ["관측 참여와 무작위 실험을 구별하는가", "공변량 조정과 매칭을 서로 다른 표본·대상 대비로 설명하는가", "매칭 후 균형 및 제외된 참여자 수를 제시하는가", "v02의 중첩 부족을 수치의 유의성과 별개로 검토하는가", "사업 이수·수강시간을 기초 교란변수로 잘못 통제하지 않는가", "임금근로자 평균임금과 전체 대상자 근로소득을 구별하는가", "추적탈락이 없는 연습 설정을 실제 현장의 결측 해결책으로 과장하지 않는가"]}}


def build(seed: int) -> dict:
    return {"id": "c03_training", "title": "디지털 재취업교육 참여와 6개월 뒤 월 근로소득",
            "policy_question": "기초 특성이 다른 교육 참여자와 비참여자의 6개월 뒤 월 근로소득 차이를 어떻게 비교할 수 있으며, 비교 가능한 대상에게 어떤 범위의 답을 제시할 수 있는가?",
            "introduction": "구직자·경력전환자를 위한 허구 교육사업이다. 한국노동패널 통합코드북의 개인 식별·성별·나이·훈련경험 개념을 참고하되 사업 참여와 전체 대상자 소득은 별도로 정의했다.",
            "target_population": "가상 재취업 지원대상 20–54세 900명; 미취업자와 경력전환을 준비하는 취업자 포함",
            "unit_of_observation": "동일한 개인; 기초조사·사업명부·6개월 추적조사를 분리 제공",
            "time_structure": "사업 이전 기초시점과 공통 사업 기준일 6개월 뒤 추적시점. 참여자만의 수료일을 추적시점으로 삼지 않는다.",
            "source_ids": ["klips"],
            "collection_notes": ["원자료의 숫자·사람·응답은 사용하지 않았다. 성별 1=남자, 2=여자와 일반 훈련경험 1·2·3, 모름/무응답 -1만 공식 통합코드북의 개념을 참고했다.", "program_participation은 자체 가상 사업 참여변수다. p__4501 일반 훈련경험과 의미가 다르다.", "소득은 미취업자 0을 포함하는 전체 대상자 월 근로소득으로 자체 정의했다. p__1642 임금근로자 월평균임금과 동일한 변수라고 주장하지 않는다.", "세 원자료의 개인키는 일대일이며 900명 모두 추적된 기본 연습이다. 일반 훈련경험 이외의 분석 필수변수에는 결측이 없다."],
            "variants": [_variant(seed + 301, "v01", False), _variant(seed + 302, "v02", True)]}
