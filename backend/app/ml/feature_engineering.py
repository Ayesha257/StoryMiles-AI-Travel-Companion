"""Feature construction identical to the supplied model's training pipeline."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import pandas as pd


BUDGET_MAP = {"low": 0, "medium": 1, "high": 2}
WEATHER_BUCKETS = ("hot", "mild", "cold")

# Maps app travel-style / interest labels to tags used in destinations.csv.
INTEREST_ALIASES: dict[str, str] = {
    "cultural": "culture",
    "culture": "culture",
    "history": "culture",
    "food": "cuisine",
    "cuisine": "cuisine",
    "relaxation": "wellness",
    "wellness": "wellness",
    "beach": "beaches",
    "beaches": "beaches",
    "shopping": "urban",
    "adventure": "adventure",
    "nightlife": "nightlife",
    "nature": "nature",
}


def _normalise_tags(values: Iterable[object] | object | None) -> set[str]:
    """Convert comma-separated tags or an iterable to a safe comparison set."""
    if values is None:
        return set()
    if isinstance(values, str):
        values = values.split(",")
    try:
        return {str(value).strip().lower() for value in values if str(value).strip()}
    except TypeError:
        return set()


def normalise_user_interests(values: Iterable[object] | object | None) -> set[str]:
    """Map user-facing interests/travel styles to destination tag vocabulary."""
    tags = _normalise_tags(values)
    return {INTEREST_ALIASES.get(tag, tag) for tag in tags}


def _normalise_budget(value: object) -> str:
    budget = str(value).strip().lower()
    if budget not in BUDGET_MAP:
        raise ValueError("budget must be one of: low, medium, high")
    return budget


def _normalise_weather(value: object) -> str:
    weather = str(value).strip().lower()
    if weather not in WEATHER_BUCKETS:
        raise ValueError("weather preference must be one of: hot, mild, cold")
    return weather


def build_feature_frame(
    *,
    destinations: pd.DataFrame,
    feature_columns: Sequence[str],
    user_budget: str,
    user_weather_preference: str,
    user_interests: Iterable[object] | None,
    user_trip_duration: int,
) -> pd.DataFrame:
    """Build one model-ready feature row per destination in saved column order.

    The numeric features and weather flags mirror ``03_train_model.py``.
    Missing or unfamiliar interest tags simply have no
    intersection with a destination's comma-separated tags.
    """
    normalised_budget = _normalise_budget(user_budget)
    normalised_weather = _normalise_weather(user_weather_preference)
    interests = normalise_user_interests(user_interests)
    user_budget_num = BUDGET_MAP[normalised_budget]
    rows: list[dict[str, int | float]] = []

    for destination in destinations.to_dict(orient="records"):
        destination_budget = _normalise_budget(destination["budget_tier"])
        destination_weather = _normalise_weather(destination["best_weather"])
        destination_duration = int(destination["ideal_duration"])
        destination_tags = _normalise_tags(destination.get("tags"))
        destination_budget_num = BUDGET_MAP[destination_budget]
        row: dict[str, int | float] = {
            "user_budget_num": user_budget_num,
            "dest_budget_num": destination_budget_num,
            "budget_diff": abs(user_budget_num - destination_budget_num),
            "interest_overlap": len(interests & destination_tags),
            "user_trip_duration": user_trip_duration,
            "dest_ideal_duration": destination_duration,
            "duration_diff": abs(user_trip_duration - destination_duration),
        }
        for weather in WEATHER_BUCKETS:
            row[f"uw_{weather}"] = int(normalised_weather == weather)
            row[f"dw_{weather}"] = int(destination_weather == weather)
        rows.append(row)

    # ``feature_columns.pkl`` is the exact training-time source of truth.
    # Reindexing both selects observed dummy columns and preserves their order.
    return pd.DataFrame(rows).reindex(columns=list(feature_columns), fill_value=0)
