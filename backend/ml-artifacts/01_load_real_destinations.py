"""
Step 1 (replacement): Load REAL destination data from the Kaggle
"Worldwide Travel Cities (Ratings and Climate)" dataset and convert it
into the same destinations.csv schema our pipeline already uses
(name, country, budget_tier, best_weather, tags, ideal_duration).

============================================================
IF THIS SCRIPT ERRORS: it means your CSV's column names are
slightly different from what's coded below. Fix is always the
same: open data/raw/worldwide_travel_cities.csv, check the real
header row, then edit the CONFIG section right below this
comment to match. Nothing else in the script needs to change.
============================================================
"""
import pandas as pd
import json
import re

# ---------------- CONFIG: edit these if your CSV's headers differ ----------------
RAW_CSV_PATH = "data/raw/worldwide_travel_cities.csv"

COL_CITY = "city"
COL_COUNTRY = "country"
COL_BUDGET = "budget_level"          # expected values like "Budget"/"Mid-range"/"Luxury"
COL_DURATION = "ideal_durations"     # expected like "3-5 days" or "Short trip (1-3 days)"
COL_CLIMATE = "avg_temp_monthly"     # expected: JSON string of month -> avg temp (Celsius)

# Rating columns (0-5 scale) used to build the `tags` field
RATING_COLS = ["culture", "adventure", "nature", "beaches", "nightlife",
               "cuisine", "wellness", "urban", "seclusion"]
TOP_N_TAGS = 3          # how many top-rated categories become this city's tags
MIN_TAG_RATING = 3.0    # don't tag a category unless it scores at least this high
# -----------------------------------------------------------------------------


def normalize_budget(val):
    if pd.isna(val):
        return "medium"
    v = str(val).lower()
    if "budget" in v or "low" in v or "cheap" in v:
        return "low"
    if "luxury" in v or "high" in v or "premium" in v:
        return "high"
    return "medium"


DURATION_LABELS = {
    "weekend": 2,
    "short trip": 4,
    "one week": 7,
    "long trip": 12,
}


def normalize_duration(val):
    """Map duration labels/lists like '["Short trip","One week"]' to a day count."""
    if pd.isna(val):
        return 5

    text = str(val).strip()
    labels: list[str] = []
    try:
        parsed = json.loads(text.replace("'", '"'))
        if isinstance(parsed, list):
            labels = [str(item).strip().lower() for item in parsed if str(item).strip()]
        elif isinstance(parsed, str):
            labels = [parsed.strip().lower()]
    except Exception:
        labels = [part.strip().lower() for part in re.split(r"[|,;/]+", text) if part.strip()]

    mapped = [DURATION_LABELS[label] for label in labels if label in DURATION_LABELS]
    if mapped:
        return int(round(sum(mapped) / len(mapped)))

    nums = [int(n) for n in re.findall(r"\d+", text)]
    if not nums:
        return 5
    return int(round(sum(nums) / len(nums)))


def normalize_weather(val):
    """avg_temp_monthly JSON looks like {"1":{"avg":3.7,"max":7.8,"min":0.4}, ...}.

    Average the monthly ``avg`` values (or bare numbers) and bucket into hot/mild/cold.
    """
    if pd.isna(val):
        return "mild"
    try:
        temps = json.loads(str(val).replace("'", '"'))
        if not isinstance(temps, dict) or not temps:
            return "mild"
        monthly = []
        for value in temps.values():
            if isinstance(value, dict):
                if "avg" in value:
                    monthly.append(float(value["avg"]))
                elif "max" in value and "min" in value:
                    monthly.append((float(value["max"]) + float(value["min"])) / 2)
            else:
                monthly.append(float(value))
        if not monthly:
            return "mild"
        avg = sum(monthly) / len(monthly)
    except Exception:
        return "mild"
    if avg >= 25:
        return "hot"
    if avg <= 12:
        return "cold"
    return "mild"


def build_tags(row):
    scores = [(col, row[col]) for col in RATING_COLS if col in row and pd.notna(row[col])]
    scores.sort(key=lambda x: x[1], reverse=True)
    top = [name for name, val in scores[:TOP_N_TAGS] if val >= MIN_TAG_RATING]
    if not top:
        top = [scores[0][0]] if scores else ["culture"]
    return ",".join(top)


def main():
    df = pd.read_csv(RAW_CSV_PATH)
    print("Loaded raw file. Columns found:")
    print(df.columns.tolist())
    print(f"Rows: {len(df)}")

    missing = [c for c in [COL_CITY, COL_COUNTRY] if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing expected columns {missing}. "
            f"Open the CSV, check real headers, and update the CONFIG section at the top of this script."
        )

    out_rows = []
    for _, row in df.iterrows():
        out_rows.append({
            "name": row[COL_CITY],
            "country": row.get(COL_COUNTRY, "Unknown"),
            "budget_tier": normalize_budget(row.get(COL_BUDGET)),
            "best_weather": normalize_weather(row.get(COL_CLIMATE)),
            "tags": build_tags(row),
            "ideal_duration": normalize_duration(row.get(COL_DURATION)),
        })

    out_df = pd.DataFrame(out_rows).dropna(subset=["name"]).drop_duplicates(subset=["name"])
    out_df.to_csv("destinations.csv", index=False)
    print(f"\nSaved {len(out_df)} real destinations to destinations.csv")
    print(out_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
