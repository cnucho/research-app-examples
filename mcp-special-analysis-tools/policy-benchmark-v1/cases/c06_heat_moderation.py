"""Synthetic outdoor-work training: continuous moderation and GLM outcomes."""
from __future__ import annotations

import numpy as np
import pandas as pd

from fixturelib import field, plan, resource


def _join(right: str) -> dict:
    return {"op": "join", "right_dataset": right, "left_on": ["worker_id"],
            "right_on": ["worker_id"], "how": "left", "cardinality": "1:1",
            "match_nulls": False, "suffixes": ["_left", "_right"], "max_output_rows": 900}


def build(seed: int) -> dict:
    variants = []
    for number in (1, 2):
        variant_seed = int(seed) + 6000 + number
        rng = np.random.default_rng(variant_seed)
        n = 900
        ids = [f"SYN-W{index:05d}" for index in range(1, n + 1)]
        age = rng.integers(20, 65, n)
        experience = np.minimum(rng.integers(0, 36, n), age-18)
        exposure = rng.uniform(1, 8, n)
        baseline_strain = rng.uniform(25, 60, n)
        training = rng.uniform(0, 12, n)
        beta_t, beta_tw = -.65, (-.13 if number == 1 else 0.0)
        base = (26 + 2.1 * exposure + .30 * baseline_strain
                + .045 * (age - 40) - .055 * experience + rng.uniform(-5, 5, n))
        individual_slope = beta_t + beta_tw * exposure
        followup_strain = base + individual_slope * training
        # All workers share the same 30-day follow-up; no unmodeled offset.
        log_rate = (-1.9 - .055 * training + .18 * exposure
                    + .012 * (age - 40) - .018 * experience)
        injury_rate = np.exp(log_rate)
        injury_count = rng.poisson(injury_rate)
        injury_any = (injury_count >= 1).astype(int)
        baseline = pd.DataFrame({"worker_id": ids, "age_years": age,
            "experience_years": experience, "baseline_outdoor_hours": exposure,
            "baseline_heat_strain": baseline_strain, "baseline_date": ["2026-05-01"] * n})
        training_register = pd.DataFrame({"worker_id": ids, "training_hours": training,
            "training_end_date": ["2026-05-31"] * n})
        followup = pd.DataFrame({"worker_id": ids, "followup_heat_strain": followup_strain,
            "injury_events": injury_count, "injury_any": injury_any,
            "followup_days": np.full(n, 30, dtype=int),
            "followup_start": ["2026-06-01"] * n, "followup_end": ["2026-06-30"] * n})
        id_field = lambda: field("worker_id", "string", "가상 작업자 번호", role="identifier")
        fk = [{"fields": ["worker_id"], "reference": {"resource": "baseline", "fields": ["worker_id"]}}]
        resources = [
            resource("baseline", "폭염 안전교육 전 작업환경 조사", baseline, [id_field(),
                field("age_years", "integer", "연령", unit="세", time="교육 전"),
                field("experience_years", "integer", "현장업무 경력", unit="년", time="교육 전"),
                field("baseline_outdoor_hours", "number", "교육 전 하루 평균 옥외작업시간", unit="시간/일", time="교육 전 7일",
                    source="working-conditions", source_variable="고온 노출 정도(Q23_c; 과거년도 통계의 개념 참고)", match="concept_adaptation",
                    question="교육 시작 전 일주일 동안, 근무일에 옥외에서 일한 시간은 하루 평균 몇 시간입니까?",
                    description="고온 작업환경 노출 개념을 참고해 별도로 만든 옥외근무 연속시간 항목이다. 과거 근로환경조사의 Q23_c 7단계 고온노출 응답을 시간으로 환산한 값이 아니며 실측 온도도 아니다."),
                field("baseline_heat_strain", "number", "교육 전 열부담 지수", unit="점(0~100)", time="교육 전",
                    question="교육 전 최근 근무일의 더위로 인한 작업부담 정도를 0~100점으로 표시하십시오.",
                    description="0 부담 없음, 100 매우 큰 부담. 자체 작성한 연속 지수이며 임상 진단점수가 아니다."),
                field("baseline_date", "string", "기초조사 기준일"),
            ], primary_key=["worker_id"]),
            resource("training", "폭염 안전교육 이수기록", training_register, [id_field(),
                field("training_hours", "number", "안전교육 이수시간", unit="시간", time="기초조사 이후, 후속관측 이전",
                    description="0~12시간의 연속 이수시간. 일률적인 교육참가 0/1 변수와 다르다."),
                field("training_end_date", "string", "교육기간 종료일"),
            ], primary_key=["worker_id"], foreign_keys=fk),
            resource("followup", "30일 현장 안전관측", followup, [id_field(),
                field("followup_heat_strain", "number", "교육 후 열부담 지수", unit="점(0~100)", time="교육 후 30일",
                    question="교육 후 30일의 근무기간에 더위로 느낀 작업부담 정도를 0~100점으로 표시하십시오.",
                    description="0 부담 없음, 100 매우 큰 부담. 기초조사와 같은 자체 연속 지수다."),
                field("injury_events", "integer", "30일 경미한 작업상 위해사건 수", unit="건/30일", time="교육 후 30일",
                    description="가상 사건등록의 건수. 실제 질병 진단, 승인 산업재해 또는 응급실 온열질환 자료가 아니다."),
                field("injury_any", "integer", "30일 위해사건 한 번 이상 여부", labels={0: "없음", 1: "있음"}, time="교육 후 30일",
                    description="injury_events가 1 이상이면 1, 0이면 0이다."),
                field("followup_days", "integer", "공통 추적 관측일수", unit="일", description="모든 작업자를 30일간 관측했다. 근로시간당 발생률의 분모는 아니다."),
                field("followup_start", "string", "추적 시작일"),
                field("followup_end", "string", "추적 종료일"),
            ], primary_key=["worker_id"], foreign_keys=fk),
        ]
        preparation = [_join("training"), _join("followup")]
        common_covariates = ["baseline_heat_strain", "age_years", "experience_years"]
        moderation = plan("moderation_heat_strain", "moderation",
            {"outcome": "followup_heat_strain", "treatment": "training_hours",
             "moderator": "baseline_outdoor_hours", "covariates": common_covariates, "id": "worker_id"},
            {"na_action": "error", "se_type": "HC3", "reference_distribution": "t", "df_method": "residual", "moderator_values": [2, 4, 6]},
            input_resource="baseline", preparation=preparation, seed=variant_seed,
            estimand="교육 전 옥외작업 하루 2·4·6시간에서 교육 1시간 증가에 대응하는 열부담 지수의 조건부 기울기",
            rationale="호스트가 연속 교육시간과 교육 전 연속 노출시간의 상호작용, 공변량, 기울기 평가점을 명시했다.")
        interaction_prep = preparation + [{"op": "derive", "name": "training_x_outdoor",
            "expression": "training_hours * baseline_outdoor_hours",
            "definition": "교육 이수시간과 교육 전 옥외작업시간의 곱. 호스트가 지정한 동일 선형모형의 교차검산용 변수다.",
            "unit": "시간^2/일"}]
        gaussian = plan("gaussian_equivalent_interaction", "regression",
            {"outcome": "followup_heat_strain", "treatment": "training_hours",
             "covariates": ["baseline_outdoor_hours", "training_x_outdoor", *common_covariates], "id": "worker_id"},
            {"na_action": "error", "estimator": "lm", "family": "gaussian", "link": "identity", "se_type": "HC3", "reference_distribution": "t", "df_method": "residual"},
            input_resource="baseline", preparation=interaction_prep, seed=variant_seed,
            estimand="동일 설계행렬을 명시적 곱 변수로 표현한 선형회귀 계수",
            rationale="moderation과 regression의 관측자료 계산 일치 확인용 계획. 이 계획은 상호작용 포함 여부를 데이터로 자동 선택하지 않는다.")
        glm_covariates = ["baseline_outdoor_hours", "age_years", "experience_years"]
        poisson = plan("poisson_30day_events", "regression",
            {"outcome": "injury_events", "treatment": "training_hours", "covariates": glm_covariates, "id": "worker_id"},
            {"na_action": "error", "estimator": "glm", "family": "poisson", "link": "log", "se_type": "HC3", "reference_distribution": "normal"},
            input_resource="baseline", preparation=preparation, seed=variant_seed,
            estimand="공통 30일 관측창의 사건 기대건수에 대한 로그선형 회귀 계수",
            rationale="모든 관측창이 30일이므로 노출기간 offset이 필요 없는 명시적 Poisson 계산이다. 실제 근로시간당 발생률로 해석하지 않는다.")
        binary = plan("binomial_any_event", "regression",
            {"outcome": "injury_any", "treatment": "training_hours", "covariates": glm_covariates, "id": "worker_id"},
            {"na_action": "error", "estimator": "glm", "family": "binomial", "link": "cloglog", "se_type": "HC3", "reference_distribution": "normal"},
            input_resource="baseline", preparation=preparation, seed=variant_seed,
            estimand="동일 30일 창에서 사건이 한 번 이상 생길 확률의 complementary-log-log 회귀 계수",
            rationale="injury_any는 동일 Poisson 사건수의 0 대 1 이상 요약이므로 P(any)=1-exp(-lambda). 호스트가 이를 명시하여 binomial cloglog 링크를 사용한다. logit 계수와 같다고 주장하지 않는다.")
        variants.append({"id": f"v{number:02d}", "seed": variant_seed, "resources": resources,
            "relationships": [{"left_resource": "baseline", "right_resource": right,
                "left_fields": ["worker_id"], "right_fields": ["worker_id"], "cardinality": "1:1",
                "expected_matched_rows": n, "expected_unmatched_left": 0,
                "description": "동일한 작업자 900명의 기초조사·교육·30일 추적자료를 개인키로 일대일 결합한다."}
                for right in ("training", "followup")],
            "evaluator": {
                "dgp": {"training_assignment": "Uniform(0,12), independent of baseline covariates in this synthetic DGP",
                    "moderator_distribution": "Uniform(1,8), measured before training",
                    "strain_equation": "26+2.1*W+0.30*baseline_strain+0.045*(age-40)-0.055*experience+beta_T*T+beta_TW*T*W+Uniform(-5,5)",
                    "beta_training": beta_t, "beta_interaction": beta_tw,
                    "conditional_training_slopes": {str(w): beta_t+beta_tw*w for w in (2, 4, 6)},
                    "count_equation": "N~Poisson(exp(-1.9-0.055*T+0.18*W+0.012*(age-40)-0.018*experience))",
                    "binary_equation": "A=1[N>=1]; P(A=1)=1-exp(-lambda); cloglog(P)=log(lambda)",
                    "followup_days": 30, "null_definition": "v02 has zero training-by-outdoor interaction; the main training slope and count effects remain nonzero.",
                    "selection": "No p-value-based filtering, repeated seed search, clipping, or outcome rounding."},
                "potential_outcomes": pd.DataFrame({"worker_id": ids,
                    "strain_if_training_0": base, "strain_if_training_4": base+4*individual_slope,
                    "strain_if_training_8": base+8*individual_slope,
                    "individual_training_slope": individual_slope,
                    "observed_strain": followup_strain, "expected_injury_count": injury_rate,
                    "probability_any_injury": 1-np.exp(-injury_rate)}),
                "reference_plans": [moderation, gaussian, poisson, binary],
                "expected_checks": [
                    {"id": "same_window", "kind": "exact_structural", "description": "followup_days is 30 for all 900 rows."},
                    {"id": "count_binary_identity", "kind": "exact_arithmetic", "description": "injury_any == int(injury_events >= 1)"},
                    {"id": "interaction_identity", "kind": "exact_arithmetic", "description": "training_x_outdoor equals the product of its two source columns."},
                    {"id": "regression_moderation_parity", "kind": "numerical_reference", "description": "동일 설계행렬의 regression과 moderation에서 적합값, 상호작용 계수, HC3 공분산, 조건부 기울기가 일치해야 한다."},
                    {"id": "simple_slope_covariance", "kind": "numerical_reference", "description": "At W=w, slope=b_T+w*b_TW and variance=V_TT+2*w*V_T,TW+w^2*V_TW,TW."},
                    {"id": "null_interaction_review", "kind": "host_review", "description": "생성모형의 상호작용 0은 표본에서 항상 p>0.05가 나와야 한다는 뜻이 아니다. 상호작용 부재와 주효과 부재를 구분한다."},
                ],
                "rubric": ["교육시간과 교육 전의 연속 노출시간을 구별하고, 2·4·6시간의 평가점과 관측범위를 표시한다.",
                           "v02에서 상호작용이 0이라는 DGP 사실을 사용자 자료에서 이미 알려진 사실처럼 설명하지 않는다.",
                           "유의하지 않은 상호작용을 효과가 동일함이 증명됐다고 해석하지 않는다.",
                           "Poisson은 사건수, binomial은 같은 관측창의 1회 이상 확률을 계산한다. 서로 다른 척도의 계수를 단순 비교하지 않는다.",
                           "binomial reference는 cloglog 링크이며 일반적인 logit 링크라고 잘못 설명하지 않는다.",
                           "관측창은 30일이며 근로시간 exposure offset이 구현됐다고 주장하지 않는다."],
            }})
    return {"id": "c06_heat_safety", "title": "폭염 안전교육 시간과 옥외작업 노출",
        "policy_question": "폭염 안전교육을 더 받았을 때 열부담과 위해사건은 얼마나 달라지는가? 교육 전 옥외작업시간에 따라 그 관계가 달라지는가?",
        "introduction": "가상 현장작업자의 기초 작업환경, 연속 교육 이수시간, 후속 30일의 열부담·사건수·사건유무를 결합한다.",
        "target_population": "가상 안전교육에 참여한 현장작업자 900명", "unit_of_observation": "작업자",
        "time_structure": "교육 전 기초조사, 1개월 교육기간, 동일 30일 후속관측창",
        "source_ids": ["working-conditions"],
        "collection_notes": ["실제 근로자·사업장·환자 자료를 사용하지 않았다. 가상 ID만 제공한다.",
            "작업환경 노출 개념을 참고했지만 공식 조사의 문항, 변수코드, 검증된 열부담 척도를 재현한 자료는 아니다.",
            "교육 전 노출시간과 교육 이수시간은 연속값이다. 임의로 고·저 집단으로 잘라 저장하지 않았다.",
            "모든 작업자의 사건 관측창은 동일한 30일이다. injury_any는 해당 창에서 injury_events가 한 건 이상인지를 기록한다.",
            "관측자료에는 교육량 배정의 외생성에 대한 실증적 보증이 없다. 정책적 인과해석은 수집 설계와 추가 정보를 검토해야 한다."],
        "variants": variants}
