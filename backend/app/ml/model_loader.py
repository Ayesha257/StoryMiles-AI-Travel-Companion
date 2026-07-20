"""Startup-loaded singleton for the supplied recommendation model artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


ARTIFACT_DIRECTORY = Path(__file__).resolve().parents[2] / "ml-artifacts"
MODEL_PATH = ARTIFACT_DIRECTORY / "recommender_model.pkl"
FEATURE_COLUMNS_PATH = ARTIFACT_DIRECTORY / "feature_columns.pkl"
DESTINATIONS_PATH = ARTIFACT_DIRECTORY / "destinations.csv"
REQUIRED_DESTINATION_COLUMNS = {
    "name",
    "country",
    "budget_tier",
    "best_weather",
    "tags",
    "ideal_duration",
}


@dataclass(frozen=True)
class RecommendationArtifacts:
    model: Any
    feature_columns: tuple[str, ...]
    destinations: pd.DataFrame


_artifacts: RecommendationArtifacts | None = None


def load_recommendation_artifacts() -> RecommendationArtifacts:
    """Load the trained model and its data once during application startup."""
    global _artifacts
    if _artifacts is not None:
        return _artifacts

    missing = [str(path) for path in (MODEL_PATH, FEATURE_COLUMNS_PATH, DESTINATIONS_PATH) if not path.is_file()]
    if missing:
        raise RuntimeError(f"Recommendation artifacts are missing: {', '.join(missing)}")

    model = joblib.load(MODEL_PATH)
    feature_columns = tuple(joblib.load(FEATURE_COLUMNS_PATH))
    destinations = pd.read_csv(DESTINATIONS_PATH)
    missing_columns = REQUIRED_DESTINATION_COLUMNS.difference(destinations.columns)
    if missing_columns:
        raise RuntimeError(f"destinations.csv is missing required columns: {sorted(missing_columns)}")
    if destinations.empty:
        raise RuntimeError("destinations.csv contains no destinations")
    if not feature_columns:
        raise RuntimeError("feature_columns.pkl contains no feature columns")

    model_columns = tuple(getattr(model, "feature_names_in_", ()))
    if model_columns and model_columns != feature_columns:
        raise RuntimeError("Model feature order does not match feature_columns.pkl")

    _artifacts = RecommendationArtifacts(
        model=model,
        feature_columns=feature_columns,
        destinations=destinations,
    )
    return _artifacts


def get_recommendation_artifacts() -> RecommendationArtifacts:
    """Return the already loaded singleton; inference must never load from disk."""
    if _artifacts is None:
        raise RuntimeError("Recommendation model has not been loaded at startup")
    return _artifacts


def get_model_health() -> dict[str, object]:
    """Return a non-loading health snapshot for readiness reporting."""
    if _artifacts is None:
        return {"status": "not_loaded"}
    return {
        "status": "ready",
        "model": type(_artifacts.model).__name__,
        "destination_count": len(_artifacts.destinations),
        "feature_count": len(_artifacts.feature_columns),
    }
