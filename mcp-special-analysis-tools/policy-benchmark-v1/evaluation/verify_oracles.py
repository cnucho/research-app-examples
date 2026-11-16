"""Verify declared arithmetic identities in already-generated fixture files.

This reads the user CSVs and curator CSV/JSON, never imports a generator, and
never fits a model.  A match concerns stored values and explicit formulae only;
it is not an assessment of identification, estimator quality, or policy effects.

Usage: python evaluation/verify_oracles.py /path/to/generated/policy-benchmark-v1
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ATOL = 1e-9
KEY_COLUMNS = ("region_id", "region_code", "year", "survey_period", "sample_person_id",
               "person_id", "application_id", "participant_id", "worker_id", "policy_id")


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig", float_precision="round_trip",
                       dtype={name: "string" for name in KEY_COLUMNS})


def _num(value):
    return np.asarray(value, dtype=float)


class _Case:
    def __init__(self, root: Path, case: str, variant: str, checks: list):
        self.prefix = f"{case}/{variant}"
        self.user = root / "user" / case / variant
        self.curator = root / "curator" / case / variant
        self.checks = checks
        self.oracle = _read_csv(self.curator / "potential_outcomes.csv")
        self.dgp = json.loads((self.curator / "dgp.json").read_text(encoding="utf-8"))

    def data(self, name: str) -> pd.DataFrame:
        return _read_csv(self.user / "data" / f"{name}.csv")

    def boolean(self, name: str, values, description: str):
        values = np.asarray(values, dtype=bool)
        self.checks.append({"id": f"{self.prefix}/{name}", "match": bool(values.size and values.all()),
                            "checked_values": int(values.size), "description": description})

    def equal(self, name: str, actual, expected, description: str, atol: float = ATOL):
        actual, expected = np.broadcast_arrays(_num(actual), _num(expected))
        finite = np.isfinite(actual) & np.isfinite(expected)
        error = np.abs(actual - expected)
        maximum = float(error[finite].max()) if finite.any() else None
        self.checks.append({"id": f"{self.prefix}/{name}",
                            "match": bool(actual.size and finite.all() and (error <= atol).all()),
                            "checked_values": int(actual.size), "absolute_tolerance": atol,
                            "relative_tolerance": 0, "maximum_absolute_error": maximum,
                            "description": description})

    def join(self, left: pd.DataFrame, right: pd.DataFrame, keys: list[str], *, name: str,
             cardinality: str = "one_to_one") -> pd.DataFrame:
        if left[keys].isna().any().any() or right[keys].isna().any().any():
            raise ValueError(f"Missing join key: {name}")
        joined = left.merge(right, on=keys, how="left", validate=cardinality, indicator=True)
        complete = (joined["_merge"] == "both").all() and len(joined) == len(left)
        if cardinality == "one_to_one":
            complete = complete and len(left) == len(right)
        self.boolean(f"{name}_key_coverage", [complete], "Declared keys join without missing or duplicated observations.")
        if not complete:
            raise ValueError(f"Incomplete declared key coverage: {name}")
        return joined.drop(columns="_merge")

    def align(self, public: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
        other = self.oracle.rename(columns={name: f"oracle__{name}"
                                           for name in self.oracle.columns if name not in keys})
        return self.join(public, other, keys, name="user_oracle")

    def common_binary_oracle(self):
        o = self.oracle
        self.boolean("binary_treatment_domain", o["treatment"].isin([0, 1]), "Oracle treatment is explicitly 0 or 1.")
        self.equal("unit_effect", o["unit_effect"], o["y1"] - o["y0"], "unit_effect = y1 - y0.")
        self.equal("observed_potential", o["observed"], np.where(o["treatment"] == 1, o["y1"], o["y0"]),
                   "Observed oracle value selects the potential outcome for the recorded treatment.")


def _heat(c: _Case):
    c.common_binary_oracle()
    a = c.align(c.data("annual_outcomes"), ["region_code", "year"])
    schedule = c.data("policy_schedule").rename(columns={"first_treat_year": "scheduled_cohort"})
    a = c.join(a, schedule, ["region_code"], name="schedule", cardinality="many_to_one")
    c.boolean("positive_population", a["population"] > 0, "The declared rate denominator is positive.")
    c.equal("count_to_report_rate", a["heat_reported_cases"] / a["population"] * 100000,
            a["oracle__observed"], "Observed surveillance count / synthetic population * 100000.")
    for suffix in ("0", "1"):
        c.equal(f"potential_{suffix}_count_to_rate", a[f"oracle__y{suffix}_reported_count"] / a["population"] * 100000,
                a[f"oracle__y{suffix}"], "The stored potential count and potential rate use the same denominator.")
    c.equal("schedule_cohort", a["oracle__first_treat_year"], a["scheduled_cohort"], "Oracle and public first-treatment years agree.", 0)
    active = (a["scheduled_cohort"] > 0) & (_num(a["year"]) >= a["scheduled_cohort"])
    c.equal("schedule_exposure", a["oracle__treatment"], active, "Exposure follows the declared absorbing adoption schedule.", 0)
    c.equal("observed_report_count", a["heat_reported_cases"],
            np.where(active, a["oracle__y1_reported_count"], a["oracle__y0_reported_count"]),
            "The public report count selects the corresponding potential count.", 0)


def _youth(c: _Case):
    c.common_binary_oracle()
    a = c.align(c.data("survey_rows"), ["region_id", "survey_period", "sample_person_id"])
    schedule = c.data("policy_schedule").rename(columns={"first_treat_wave": "scheduled_wave"})
    a = c.join(a, schedule, ["region_id"], name="schedule", cardinality="many_to_one")
    c.equal("survey_period_code", a["survey_period"], a["survey_year"] * 10 + a["survey_half"], "YYYYH code follows the public year and half-year.", 0)
    c.equal("continuous_wave", a["wave_index"], (a["survey_year"] - 2021) * 2 + a["survey_half"], "Consecutive wave index is distinct from numeric differences in YYYYH codes.", 0)
    c.equal("oracle_wave", a["oracle__wave_index"], a["wave_index"], "Oracle and public wave indices agree.", 0)
    active = (a["scheduled_wave"] > 0) & (a["wave_index"] >= a["scheduled_wave"])
    c.equal("schedule_exposure", a["oracle__treatment"], active, "Exposure follows the public regional schedule.", 0)
    c.equal("public_income", a["monthly_earnings_10kkrw"], a["oracle__observed"], "Public income in 10,000 KRW/month equals the aligned oracle observation.")
    c.equal("observed_employment", a["employed"], np.where(active, a["oracle__employment_y1"], a["oracle__employment_y0"]), "Public employment selects the recorded potential employment state.", 0)
    c.boolean("employment_domain", a["employed"].isin([0, 1]), "Employment is binary.")
    c.equal("unemployed_income_zero", a.loc[a["employed"] == 0, "monthly_earnings_10kkrw"], 0,
            "Declared nonemployment income is zero, not missing.", 0)
    q, target = a["oracle__degree_sampling_probability"], float(c.dgp["population_degree_share"])
    expected_weight = np.where(a["college_completed_pre_policy"] == 1, target / q, (1 - target) / (1 - q))
    c.equal("sampling_probability_ratio", a["survey_weight"], expected_weight, "Weights equal the declared sampling-probability ratios; no exact sample-composition equality is imposed.")
    c.equal("weight_storage", a["survey_weight"], a["oracle__survey_weight"], "Public and oracle copies of the weights agree.")


def _training(c: _Case):
    c.common_binary_oracle()
    a = c.join(c.data("baseline"), c.data("program_register"), ["person_id"], name="register")
    a = c.join(a, c.data("followup_6m"), ["person_id"], name="followup")
    a = c.align(a, ["person_id"])
    c.equal("recorded_participation", a["program_participation"], a["oracle__treatment"], "Public participation and oracle exposure agree.", 0)
    c.equal("public_income", a["followup_earnings_10kkrw"], a["oracle__observed"], "Public follow-up income equals the aligned observed potential outcome.")
    c.equal("observed_employment", a["followup_employed"], np.where(a["program_participation"] == 1, a["oracle__employment_y1"], a["oracle__employment_y0"]), "Follow-up employment selects its recorded potential state.", 0)
    for state, outcome in (("baseline_employed", "baseline_earnings_10kkrw"), ("followup_employed", "followup_earnings_10kkrw")):
        c.boolean(f"{state}_domain", a[state].isin([0, 1]), "Employment is binary.")
        c.equal(f"{state}_zero", a.loc[a[state] == 0, outcome], 0, "The declared all-person earnings variable assigns zero to nonemployment.", 0)
    c.equal("followup_interval", a["followup_months"], 6, "All records use the declared six-month follow-up.", 0)
    truth = c.dgp["finite_sample_truth"]
    c.equal("stored_finite_ate", a["oracle__unit_effect"].mean(), truth["ate_all_900"], "Stored finite-sample ATE is an arithmetic mean of potential contrasts, not a fitted estimate.")
    c.equal("stored_finite_att", a.loc[a["program_participation"] == 1, "oracle__unit_effect"].mean(), truth["att_all_observed_participants"], "Stored full-participant ATT is the mean of that declared subset's potential contrasts.")


def _insulation(c: _Case):
    a = c.join(c.data("applications"), c.data("awards"), ["application_id"], name="awards")
    a = c.join(a, c.data("bills"), ["application_id"], name="bills")
    a = c.align(a, ["application_id"])
    rules = c.data("policy_rules").set_index("policy_id", verify_integrity=True)
    for label, column in (("SYN-INSULATION", "insulation_grant"), ("SYN-APPLIANCE", "appliance_grant")):
        rule = rules.loc[label]
        expected = int(rule["active"]) * (a["need_score"] >= float(rule["cutoff_score"]))
        c.equal(f"{column}_threshold", a[column], expected, "Recorded receipt follows the declared active policy and threshold rule.", 0)
    c.equal("half_point_scores", a["need_score"] * 2, np.rint(a["need_score"] * 2), "Scores are recorded on the declared half-point grid.", 0)
    for when in ("baseline", "followup"):
        c.equal(f"{when}_bill", a[f"{when}_bill_krw"], np.rint(1800 + 230 * a[f"{when}_kwh"]), "Declared synthetic tariff: round(1800 + 230 * kWh), in KRW.", 0)
    insulation, appliance = c.dgp["insulation_effect_kwh"], c.dgp["appliance_effect_kwh"]
    base = a["oracle__y_no_support_kwh"]
    c.equal("insulation_potential", a["oracle__y_insulation_only_kwh"] - base, insulation, "Potential contrast for insulation alone.")
    c.equal("appliance_potential", a["oracle__y_appliance_only_kwh"] - base, appliance, "Potential contrast for appliance support alone.")
    c.equal("both_potential", a["oracle__y_both_kwh"] - base, insulation + appliance, "Declared additive two-policy potential contrast.")
    observed = base + insulation * a["insulation_grant"] + appliance * a["appliance_grant"]
    c.equal("public_kwh", a["followup_kwh"], observed, "Public kWh selects the potential outcome for the actual two-policy receipt vector.")
    c.equal("oracle_observed_kwh", a["oracle__observed_followup_kwh"], a["followup_kwh"], "Public and oracle observed kWh agree.")


def _digital(c: _Case):
    a = c.data("baseline")
    for right in ("assignments", "mediator_survey", "performance"):
        a = c.join(a, c.data(right), ["participant_id"], name=right)
    a = c.align(a, ["participant_id"])
    coefficient = c.dgp["coefficients"]
    alpha, beta, direct = coefficient["a"], coefficient["b"], coefficient["direct"]
    items = a[["confidence_navigation", "confidence_submission", "confidence_recovery"]]
    c.boolean("slider_range", (items >= 0) & (items <= 100), "Declared slider responses lie in 0–100.")
    c.boolean("task_score_range", a["service_task_score"].between(0, 100), "Declared task score lies in 0–100.")
    c.boolean("offer_domain", a["training_offer"].isin([0, 1]), "Recorded offer is binary.")
    c.equal("mediator_potential_contrast", a["oracle__mediator_if_offer"] - a["oracle__mediator_if_no_offer"], alpha, "Stored mediator potential contrast is the declared a coefficient.")
    c.equal("three_item_index", items.mean(axis=1), a["oracle__mediator_if_no_offer"] + alpha * a["training_offer"], "The declared equal-weight index is the arithmetic mean of all three observed items.")
    nie = a["oracle__y_1_m1"] - a["oracle__y_1_m0"]
    nde = a["oracle__y_1_m0"] - a["oracle__y_0_m0"]
    c.equal("nie_arithmetic", nie, alpha * beta, "Cross-world potential contrast equals a*b in the explicitly stored structural model.")
    c.equal("nde_arithmetic", nde, direct, "Cross-world direct contrast equals the stored direct coefficient.")
    c.equal("nie_storage", a["oracle__natural_indirect_effect"], nie, "Stored NIE is its potential-outcome difference.")
    c.equal("nde_storage", a["oracle__natural_direct_effect"], nde, "Stored NDE is its potential-outcome difference.")
    c.equal("other_mediator_contrast", a["oracle__y_0_m1"] - a["oracle__y_0_m0"], alpha * beta, "No-treatment mediator contrast follows the same declared additive equation.")
    actual = np.where(a["training_offer"] == 1, a["oracle__y_1_m1"], a["oracle__y_0_m0"])
    c.equal("public_score", a["service_task_score"], actual, "Observed task score selects the potential outcome for the recorded offer.")
    c.equal("oracle_observed_score", a["oracle__observed_score"], a["service_task_score"], "Public and oracle observed scores agree.")
    dates = [pd.to_datetime(a[col], errors="coerce") for col in ("baseline_date", "assignment_date", "mediator_date", "outcome_date")]
    c.boolean("measurement_date_order", (dates[0] < dates[1]) & (dates[1] < dates[2]) & (dates[2] < dates[3]), "Recorded measurement dates have the declared strict temporal order.")


def _safety(c: _Case):
    a = c.join(c.data("baseline"), c.data("training"), ["worker_id"], name="training")
    a = c.join(a, c.data("followup"), ["worker_id"], name="followup")
    a = c.align(a, ["worker_id"])
    slope = c.dgp["beta_training"] + c.dgp["beta_interaction"] * a["baseline_outdoor_hours"]
    c.equal("conditional_slope", a["oracle__individual_training_slope"], slope, "Stored structural slope follows beta_T + beta_TW * baseline outdoor hours.")
    base = a["oracle__strain_if_training_0"]
    for dose in (4, 8):
        c.equal(f"potential_dose_{dose}", a[f"oracle__strain_if_training_{dose}"] - base, dose * slope, "Stored dose contrast follows the declared linear potential-outcome function.")
    c.equal("public_strain", a["followup_heat_strain"], base + a["training_hours"] * slope, "Public strain equals the potential-outcome function at recorded training hours.")
    c.equal("oracle_observed_strain", a["oracle__observed_strain"], a["followup_heat_strain"], "Public and oracle observed strain agree.")
    c.boolean("strain_range", a["followup_heat_strain"].between(0, 100), "The declared strain index lies in 0–100.")
    c.boolean("count_domain", (a["injury_events"] >= 0) & (a["injury_events"] == np.floor(a["injury_events"])), "The declared event count is a nonnegative integer.")
    c.equal("count_to_binary", a["injury_any"], a["injury_events"] >= 1, "Any-event flag equals one if and only if the count is at least one.", 0)
    c.equal("common_window", a["followup_days"], c.dgp["followup_days"], "Recorded observation windows equal the declared 30 days.", 0)
    days = (pd.to_datetime(a["followup_end"], errors="coerce") - pd.to_datetime(a["followup_start"], errors="coerce")).dt.days + 1
    c.equal("calendar_window", days, a["followup_days"], "Inclusive start/end dates agree with recorded observation days.", 0)
    expected_count = np.exp(-1.9 - .055 * a["training_hours"] + .18 * a["baseline_outdoor_hours"]
                            + .012 * (a["age_years"] - 40) - .018 * a["experience_years"])
    c.equal("declared_count_mean", a["oracle__expected_injury_count"], expected_count, "Stored expected count follows the explicitly declared generator equation; observed counts are not required to equal it.")
    probability = a["oracle__probability_any_injury"]
    c.equal("poisson_any_probability", probability, -np.expm1(-expected_count), "Declared P(any) equals 1-exp(-lambda).")
    c.equal("cloglog_identity", np.log(-np.log1p(-probability)), np.log(expected_count), "The declared complementary-log-log probability transform equals log(lambda).")


CHECKERS = {
    "c01_heat_shelters": _heat,
    "c02_youth_transport": _youth,
    "c03_training": _training,
    "c04_home_insulation": _insulation,
    "c05_digital_service": _digital,
    "c06_heat_safety": _safety,
}


def verify_oracles(root: str | Path) -> dict:
    """Return mechanical checks against stored CSV/JSON without regenerating data."""
    root = Path(root).resolve()
    checks = []
    for case, checker in CHECKERS.items():
        for variant in ("v01", "v02"):
            try:
                checker(_Case(root, case, variant, checks))
            except Exception as error:
                checks.append({"id": f"{case}/{variant}/input_integrity", "match": False,
                               "error_type": type(error).__name__, "error": str(error),
                               "description": "Stored inputs could not complete the declared arithmetic checks."})
    matched = sum(item["match"] is True for item in checks)
    return {"checks": checks, "count": len(checks), "passed": bool(checks) and matched == len(checks),
            "matched_count": matched}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Generated root containing user/ and curator/.")
    result = verify_oracles(parser.parse_args().root)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    raise SystemExit(0 if result["passed"] else 1)
