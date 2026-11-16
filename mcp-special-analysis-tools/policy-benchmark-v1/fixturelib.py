"""Authoring helpers for explicit, AI-designed synthetic fixtures.

This module records specifications; it does not choose scientific designs,
recommend estimators, interpret findings, or certify causal identification.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

VERSION = "policy-benchmark-v1"
SEED = 20261116


def field(name: str, kind: str, label: str, *, role: str = "context",
          unit: str = "", description: str = "", labels: dict | None = None,
          missing: list | None = None, source: str = "synthetic-design",
          source_variable: str = "", match: str = "synthetic_only",
          question: str = "", time: str = "", **extra: Any) -> dict:
    """A field declaration; no inferred meanings or measurement levels."""
    return dict(name=name, type=kind, title=label, description=description or label,
                role=role, unit=unit, value_labels=labels or {},
                missing_values=missing or [], source_id=source,
                source_variable=source_variable, source_match=match,
                question=question, time_reference=time, **extra)


def resource(name: str, title: str, data: pd.DataFrame | list[dict],
             fields: list[dict], *, primary_key: list[str] | None = None,
             foreign_keys: list[dict] | None = None, **extra: Any) -> dict:
    frame = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    if list(frame.columns) != [f["name"] for f in fields]:
        raise ValueError(f"Explicit field order does not match {name}")
    return dict(name=name, title=title, frame=frame, fields=fields,
                primary_key=primary_key or [], foreign_keys=foreign_keys or [], **extra)


def plan(plan_id: str, method: str, variables: dict, options: dict, *,
         input_resource: str, estimand: str, rationale: str,
         confidence_level: float = .95, seed: int = SEED,
         preparation: list[dict] | None = None) -> dict:
    """Host-authored reference execution, stored outside the user bundle."""
    return dict(id=plan_id, input_resource=input_resource,
                preparation=preparation or [],
                plan=dict(method=method, variables=variables, options=options,
                          confidence_level=confidence_level, seed=seed,
                          estimand=estimand, rationale=rationale, purpose="reference"))


def logistic(x):
    return 1 / (1 + np.exp(-np.asarray(x)))


def serializable(value):
    if isinstance(value, dict):
        return {str(k): serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(v) for v in value]
    if isinstance(value, np.ndarray):
        return serializable(value.tolist())
    if isinstance(value, np.generic):
        return serializable(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value
