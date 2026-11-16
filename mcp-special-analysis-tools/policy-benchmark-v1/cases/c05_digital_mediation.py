"""Synthetic digital-service training and simple observed-variable mediation."""
from __future__ import annotations

import numpy as np
import pandas as pd

from fixturelib import field, plan, resource


def _join(right: str) -> dict:
    return {"op": "join", "right_dataset": right, "left_on": ["participant_id"],
            "right_on": ["participant_id"], "how": "left", "cardinality": "1:1",
            "match_nulls": False, "suffixes": ["_left", "_right"], "max_output_rows": 800}


def build(seed: int) -> dict:
    variants = []
    for number in (1, 2):
        variant_seed = int(seed) + 5000 + number
        rng = np.random.default_rng(variant_seed)
        n = 800
        ids = [f"SYN-D{index:05d}" for index in range(1, n + 1)]
        age = rng.integers(35, 76, n)
        education = rng.integers(6, 19, n)
        competence = rng.uniform(25, 70, n)
        program = rng.binomial(1, .5, n)
        latent_support = rng.uniform(-1.5, 1.5, n)
        latent_m = 4.0 if number == 2 else 0.0
        latent_y = 7.0 if number == 2 else 0.0
        a, b, direct = 6.0, .45, 2.5
        m0 = (28 + .28 * competence + .65 * (education - 12)
              + latent_m * latent_support + rng.uniform(-4, 4, n))
        m1 = m0 + a
        observed_m = m0 + a * program
        # Three explicitly authored continuous sliders have an exact mean index.
        # Balanced item deviations preserve an auditable index without clipping.
        item_a = rng.uniform(-3, 3, n)
        item_b = rng.uniform(-3, 3, n)
        items = [observed_m + item_a, observed_m + item_b, observed_m - item_a - item_b]
        observed_index = (items[0] + items[1] + items[2]) / 3
        m0 = observed_index - a * program
        m1 = m0 + a
        y_base = (21 + .22 * competence - .045 * (age - 50)
                  + .35 * (education - 12) + latent_y * latent_support
                  + rng.uniform(-5, 5, n))
        y0m0 = y_base + b * m0
        y1m0 = y_base + direct + b * m0
        y0m1 = y_base + b * m1
        y1m1 = y_base + direct + b * m1
        observed_y = y_base + direct * program + b * observed_index

        baseline = pd.DataFrame({"participant_id": ids, "age_years": age,
            "education_years": education, "baseline_competence": competence,
            "baseline_date": ["2026-03-01"] * n})
        assignments = pd.DataFrame({"participant_id": ids, "training_offer": program,
            "assignment_date": ["2026-03-15"] * n})
        mediator = pd.DataFrame({"participant_id": ids,
            "confidence_navigation": items[0], "confidence_submission": items[1],
            "confidence_recovery": items[2], "mediator_date": ["2026-05-01"] * n})
        outcomes = pd.DataFrame({"participant_id": ids, "service_task_score": observed_y,
            "outcome_date": ["2026-08-01"] * n})
        id_field = lambda: field("participant_id", "string", "가상 참여자 번호", role="identifier")
        fk = [{"fields": ["participant_id"], "reference": {"resource": "baseline", "fields": ["participant_id"]}}]
        resources = [
            resource("baseline", "디지털 민원지원 교육 사전조사", baseline, [id_field(),
                field("age_years", "integer", "연령", unit="세", time="교육 배정 전"),
                field("education_years", "integer", "총 교육연수", unit="년", time="교육 배정 전"),
                field("baseline_competence", "number", "사전 디지털 과제 역량점수", unit="점(0~100)",
                      source="digital-divide", source_variable="디지털정보화 역량", match="concept_adaptation", time="교육 배정 전",
                      description="디지털 역량이라는 조사영역을 참고해 새로 만든 연속 과제점수. 공인 척도나 실제 조사 변수코드가 아니다."),
                field("baseline_date", "string", "사전조사일"),
            ], primary_key=["participant_id"]),
            resource("assignments", "교육 제공 배정기록", assignments, [id_field(),
                field("training_offer", "integer", "가상 교육 제공 배정", labels={0: "대기집단", 1: "교육 제공"},
                      description="참여 신청자에게 배정한 교육 제공 여부. 모든 배정자는 지정 일정을 이행했다는 이 사례의 수집조건이다."),
                field("assignment_date", "string", "교육 배정일"),
            ], primary_key=["participant_id"], foreign_keys=fk),
            resource("mediator_survey", "교육 후 자기효능감 문항", mediator, [id_field(),
                field("confidence_navigation", "number", "필요한 민원서비스 찾기 자신감", unit="0~100 연속 슬라이더", time="교육 후, 수행평가 전",
                      question="온라인에서 나에게 필요한 공공 민원서비스를 스스로 찾을 자신이 어느 정도 있습니까?",
                      description="0 전혀 자신 없음, 100 매우 자신 있음. 자체 작성 문항이며 검증된 척도를 그대로 사용한 것이 아니다."),
                field("confidence_submission", "number", "신청서 제출 자신감", unit="0~100 연속 슬라이더", time="교육 후, 수행평가 전",
                      question="온라인 민원 신청서에 필요한 내용을 입력하고 제출할 자신이 어느 정도 있습니까?",
                      description="0 전혀 자신 없음, 100 매우 자신 있음. 자체 작성 문항이다."),
                field("confidence_recovery", "number", "오류 해결 자신감", unit="0~100 연속 슬라이더", time="교육 후, 수행평가 전",
                      question="온라인 민원 처리 중 실수나 오류가 나도 도움말을 찾아 다시 시도할 자신이 어느 정도 있습니까?",
                      description="0 전혀 자신 없음, 100 매우 자신 있음. 자체 작성 문항이다."),
                field("mediator_date", "string", "자기효능감 조사일"),
            ], primary_key=["participant_id"], foreign_keys=fk),
            resource("performance", "후속 민원과제 수행평가", outcomes, [id_field(),
                field("service_task_score", "number", "후속 민원과제 수행점수", unit="점(0~100)", time="자기효능감 조사 이후",
                      description="가상 평가과제의 연속 점수. NIA 조사와 같은 문항이나 공인 검사점수가 아니다."),
                field("outcome_date", "string", "후속 평가일"),
            ], primary_key=["participant_id"], foreign_keys=fk),
        ]
        preparation = [_join("assignments"), _join("mediator_survey"), _join("performance"),
            {"op": "derive", "name": "self_efficacy_index",
             "expression": "(confidence_navigation + confidence_submission + confidence_recovery) / 3",
             "definition": "세 자기효능감 연속 문항의 동일가중 산술평균. 결측 없이 모두 응답한 자료이다.",
             "unit": "점(0~100)"}]
        reference = plan("simple_mediation", "mediation",
            {"outcome": "service_task_score", "treatment": "training_offer", "mediator": "self_efficacy_index",
             "covariates": ["baseline_competence", "age_years", "education_years"], "id": "participant_id"},
            {"na_action": "error", "estimator": "ML", "bootstrap_samples": 499, "bootstrap_ci": "perc", "fixed_x": True},
            input_resource="baseline", preparation=preparation, seed=variant_seed,
            estimand="관측변수 선형 모형의 a, b, direct, a*b 및 direct+a*b. 인과적 자연간접효과 해석은 추가 가정에 의존한다.",
            rationale="호스트가 지정한 단일 매개변수의 가산 선형모형이며 Hayes model 4에 해당하는 기본 구조이다. PROCESS 전체 모형군을 구현하거나 공식 매크로와 동일하다고 주장하지 않는다.")
        variants.append({"id": f"v{number:02d}", "seed": variant_seed,
            "resources": resources,
            "relationships": [{"left_resource": "baseline", "right_resource": right,
                "left_fields": ["participant_id"], "right_fields": ["participant_id"], "cardinality": "1:1",
                "expected_matched_rows": n, "expected_unmatched_left": 0,
                "description": "동일한 신청자 800명의 사전조사·배정·중간조사·후속평가를 개인키로 일대일 결합한다."}
                for right in ("assignments", "mediator_survey", "performance")],
            "evaluator": {
                "dgp": {"assignment": "independent Bernoulli(0.5) randomized program offer",
                    "mediator_equation": "M=28+0.28*baseline_competence+0.65*(education_years-12)+a*T+u_m*U+e_m",
                    "outcome_equation": "Y=21+0.22*baseline_competence-0.045*(age_years-50)+0.35*(education_years-12)+direct*T+b*M+u_y*U+e_y",
                    "errors": {"U": "Uniform(-1.5,1.5)", "e_m": "Uniform(-4,4)", "e_y": "Uniform(-5,5)"},
                    "coefficients": {"a": a, "b": b, "direct": direct, "unobserved_mediator_loading": latent_m, "unobserved_outcome_loading": latent_y},
                    "population_natural_indirect_effect": a*b, "population_natural_direct_effect": direct,
                    "population_total_effect": direct+a*b,
                    "item_construction": "Three continuous sliders are M+d1, M+d2, M-d1-d2; their mean is the measured M. No rounding or clipping.",
                    "causal_limit": "v02: treatment is randomized but the mediator-outcome relation is confounded by omitted U. The observed a*b estimand need not equal the structural natural indirect effect.",
                    "selection": "One declared seed per variant; no selection by p-values, coefficient sign, or interval coverage."},
                "potential_outcomes": pd.DataFrame({"participant_id": ids, "unobserved_support": latent_support,
                    "mediator_if_no_offer": m0, "mediator_if_offer": m1,
                    "y_0_m0": y0m0, "y_1_m0": y1m0, "y_0_m1": y0m1, "y_1_m1": y1m1,
                    "natural_indirect_effect": y1m1-y1m0, "natural_direct_effect": y1m0-y0m0,
                    "observed_score": observed_y}),
                "reference_plans": [reference],
                "expected_checks": [
                    {"id": "index_identity", "kind": "exact_arithmetic", "description": "derived self_efficacy_index == mean(three observed slider items), allowing only floating-point arithmetic tolerance", "absolute_tolerance": 1e-12},
                    {"id": "temporal_order", "kind": "exact_structural", "description": "baseline_date < assignment_date < mediator_date < outcome_date"},
                    {"id": "crossworld_identity", "kind": "oracle_arithmetic", "description": "y_1_m1-y_1_m0=a*b; y_1_m0-y_0_m0=direct", "absolute_tolerance": 1e-12},
                    {"id": "lavaan_parity", "kind": "numerical_reference", "description": "동일 모형 문법, seed, 499회 bootstrap, fixed.x로 lavaan::sem을 직접 실행해 비교한다. 유한표본 추정치와 DGP 계수의 정확한 일치는 요구하지 않는다."},
                    {"id": "mediation_identification", "kind": "host_review", "description": "교육 배정 무작위화만으로 매개-결과 관계의 무교란이 확보되지는 않는다는 해석을 확인한다."},
                ],
                "rubric": ["검증된 기존 척도라고 표현하지 않고 자체 문항과 평균점수 구성을 설명한다.",
                           "총 효과, 직접 경로계수, 경로곱 간접효과를 구별한다.",
                           "단순 관측변수 매개구조만 다룬다. 다중매개·잠재변수 SEM·PROCESS 전체 모형군을 주장하지 않는다.",
                           "v02의 U는 사용자 자료에 없으므로 AI가 그 존재를 발견했다고 요구하지 않는다. 관측자료만으로 배제할 수 없는 매개-결과 교란 가능성을 설명하는지를 평가한다.",
                           "bootstrap 횟수와 오류/비허용 반복을 보고하고 특정 유의성이나 신뢰구간 포함을 정답조건으로 삼지 않는다."],
            }})
    return {"id": "c05_digital_service", "title": "디지털 민원교육과 자기효능감",
        "policy_question": "디지털 민원교육 제공이 후속 민원과제 수행을 높이는가? 교육 이후 자기효능감은 그 관계를 어떻게 설명하는가?",
        "introduction": "교육 전 기초역량, 교육 제공 배정, 교육 후 자기효능감, 이후 수행평가를 서로 다른 파일로 제공하는 완전 가상 사례이다.",
        "target_population": "가상 디지털 민원지원 교육 신청 성인 800명", "unit_of_observation": "신청자",
        "time_structure": "사전조사 → 교육 배정 → 자기효능감 조사 → 후속 수행평가",
        "source_ids": ["digital-divide"],
        "collection_notes": ["교육 제공은 신청자 안에서 무작위 배정한 설정이다. 신청자 모집 자체가 모집단의 무작위표집이라는 뜻은 아니다.",
            "NIA 디지털정보격차 조사의 접근·역량·활용 영역을 개념적으로 참고했다. 변수명·문항·점수·인과구조는 자체 설계다.",
            "자기효능감은 0~100 연속 슬라이더 세 문항으로 받는다. 이 사례에서 모든 문항에 응답했으며 임의 대체한 결측값은 없다.",
            "각 파일은 참여자 번호로 1:1 결합한다. 이름·연락처·실제 개인의 기록은 없다."],
        "variants": variants}
