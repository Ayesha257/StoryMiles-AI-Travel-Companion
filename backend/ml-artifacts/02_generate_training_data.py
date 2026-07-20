"""
Step 2: Generate synthetic (user, destination) -> match_score training pairs.

Why synthetic: we have no real user interaction data yet (cold start).
We simulate realistic users and score each user-destination pair using
rule logic + random noise. This gives the model real patterns to learn
(non-linear interactions between budget/weather/interest overlap) instead
of us hand-writing the weights ourselves.

IMPORTANT: once you have real users rating trips/destinations in your app,
replace this synthetic data with real (user, destination, rating) rows
and re-run 03_train_model.py — the rest of the pipeline doesn't change.
"""
import pandas as pd
import numpy as np
import random

random.seed(42)
np.random.seed(42)

dest_df = pd.read_csv("destinations.csv")
# Keep synthetic user interests in the same vocabulary as destinations.csv tags
# (and the runtime aliases in app.ml.feature_engineering).
ALL_INTERESTS = ["beaches", "adventure", "nightlife", "nature", "wellness",
                  "culture", "cuisine", "urban", "seclusion"]
INTEREST_ALIASES = {
    "beach": "beaches",
    "food": "cuisine",
    "history": "culture",
    "shopping": "urban",
    "relaxation": "wellness",
}
BUDGETS = ["low", "medium", "high"]
WEATHERS = ["hot", "mild", "cold"]

N_USERS = 2000

def normalize_interests(values):
    return {INTEREST_ALIASES.get(str(value).strip().lower(), str(value).strip().lower()) for value in values if str(value).strip()}

def random_user():
    return {
        "budget": random.choice(BUDGETS),
        "weather_pref": random.choice(WEATHERS),
        "interests": random.sample(ALL_INTERESTS, k=random.randint(2, 4)),
        "trip_duration": random.randint(3, 12),
    }

def budget_rank(b):
    return {"low": 0, "medium": 1, "high": 2}[b]

def score_pair(user, dest):
    """Ground-truth-ish scoring rule used ONLY to generate training labels."""
    # Budget closeness (not just match/no-match — being 1 tier off is partially okay)
    budget_diff = abs(budget_rank(user["budget"]) - budget_rank(dest["budget_tier"]))
    budget_score = max(0, 1 - budget_diff * 0.5)

    # Weather match
    weather_score = 1.0 if user["weather_pref"] == dest["best_weather"] else 0.3

    # Interest overlap (Jaccard-ish)
    dest_tags = {tag.strip().lower() for tag in str(dest["tags"]).split(",") if tag.strip()}
    user_interests = normalize_interests(user["interests"])
    overlap = len(dest_tags & user_interests)
    interest_score = overlap / max(len(user_interests), 1)

    # Duration closeness
    dur_diff = abs(user["trip_duration"] - dest["ideal_duration"])
    duration_score = max(0, 1 - dur_diff / 10)

    base = (0.30 * budget_score + 0.25 * weather_score +
            0.30 * interest_score + 0.15 * duration_score)

    # Add noise to mimic real human unpredictability (people don't follow rules exactly)
    noisy = base + np.random.normal(0, 0.08)
    return float(np.clip(noisy, 0, 1))

rows = []
for _ in range(N_USERS):
    user = random_user()
    # each synthetic user rates a handful of destinations (like real usage: not everyone rates everything)
    sampled_dests = dest_df.sample(n=random.randint(3, 8), random_state=random.randint(0, 99999))
    for _, dest in sampled_dests.iterrows():
        s = score_pair(user, dest)
        rows.append({
            "user_budget": user["budget"],
            "user_weather_pref": user["weather_pref"],
            "user_interests": ",".join(user["interests"]),
            "user_trip_duration": user["trip_duration"],
            "dest_name": dest["name"],
            "dest_budget_tier": dest["budget_tier"],
            "dest_best_weather": dest["best_weather"],
            "dest_tags": dest["tags"],
            "dest_ideal_duration": dest["ideal_duration"],
            "match_score": s,
        })

train_df = pd.DataFrame(rows)
train_df.to_csv("training_pairs.csv", index=False)
print(f"Generated {len(train_df)} training rows from {N_USERS} synthetic users")
print(train_df.head())
