"""Run fresh LCA and MCA calculations on the generated public example."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lca_mca.contracts import ModelSpec
from lca_mca.importers import import_dataset
from lca_mca.hashing import frame_sha256
from lca_mca.lca import fit_class_range
from lca_mca.mca import run_mca

ATTITUDES = ["att_cost", "att_convenience", "att_environment", "att_safety",
             "att_digital", "att_transit", "att_flexibility", "att_ownership"]
CHOICES = ["choice_commute", "choice_priority", "choice_service", "choice_trip", "choice_info"]


def verify(folder: Path) -> dict:
    csv = import_dataset(folder / "mobility_survey.csv", codebook=folder / "codebook.json")
    sav = import_dataset(folder / "mobility_survey.sav")
    assert csv.status == sav.status == "ok"
    assert csv.frame is not None and sav.frame is not None
    assert csv.frame.shape == sav.frame.shape == (1800, 21)
    assert csv.frame.astype(str).equals(sav.frame.astype(str)), "CSV and SAV values differ"
    assert csv.manifest is not None and sav.manifest is not None
    income = next(item for item in csv.manifest.variables if item.name == "income_group")
    assert any("99" in rule.values and rule.source == "codebook" for rule in income.missing_rules)
    data_hash = csv.manifest.sha256
    working_hash = frame_sha256(csv.frame)
    mca = run_mca(csv.frame, CHOICES, data_hash=data_hash, working_hash=working_hash)
    assert mca.success and mca.n_used == 1800
    search = fit_class_range(csv.frame, ModelSpec(indicators=ATTITUDES, class_min=1,
                                                  class_max=3, n_init=5, max_iter=80, random_state=0),
                             data_hash=data_hash, working_hash=working_hash)
    assert any(run.success and run.k > 1 for run in search.runs)
    return {"rows": 1800, "columns": 21, "csv_sav_parity": True,
            "mca_success": mca.success, "mca_n": mca.n_used,
            "lca": [{"k": run.k, "success": run.success, "n": run.n_valid,
                     "bic": run.bic} for run in search.runs]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    print(json.dumps(verify(parser.parse_args().folder), ensure_ascii=False, indent=2))
