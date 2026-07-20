"""
Step 3: Feature engineering + training.

Model choice: RandomForestRegressor.
Why: handles mixed categorical/numeric features well, doesn't need feature
scaling, resists overfitting on small-medium datasets, and needs zero
tuning to get a solid baseline. A neural net (MLPRegressor) would work too
but needs more data + tuning to beat this for a dataset this size -- not
worth it for a POC. This is a defensible, explainable choice for a viva.

Target: match_score (0-1, regression) -- NOT a classification of
match/no-match. Regression lets us rank destinations by predicted score,
which is what a recommender needs.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder
from sklearn.metrics import mean_squared_error, r2_score
import joblib

df = pd.read_csv("training_pairs.csv")

# ---- Feature engineering ----
# Categorical one-hot: budget tiers, weather
budget_map = {"low": 0, "medium": 1, "high": 2}
weather_ohe = pd.get_dummies(df[["user_weather_pref", "dest_best_weather"]], prefix=["uw", "dw"])

df["user_budget_num"] = df["user_budget"].map(budget_map)
df["dest_budget_num"] = df["dest_budget_tier"].map(budget_map)
df["budget_diff"] = (df["user_budget_num"] - df["dest_budget_num"]).abs()

# Interest overlap as a numeric feature (intersection count in tag vocabulary)
INTEREST_ALIASES = {
    "beach": "beaches",
    "food": "cuisine",
    "history": "culture",
    "shopping": "urban",
    "relaxation": "wellness",
}

def normalize_tags(value):
    return {
        INTEREST_ALIASES.get(tag.strip().lower(), tag.strip().lower())
        for tag in str(value).split(",")
        if tag.strip()
    }

def overlap_count(user_interests_str, dest_tags_str):
    return len(normalize_tags(user_interests_str) & normalize_tags(dest_tags_str))

df["interest_overlap"] = df.apply(
    lambda r: overlap_count(r["user_interests"], r["dest_tags"]), axis=1
)
df["duration_diff"] = (df["user_trip_duration"] - df["dest_ideal_duration"]).abs()

feature_cols = ["user_budget_num", "dest_budget_num", "budget_diff",
                 "interest_overlap", "user_trip_duration",
                 "dest_ideal_duration", "duration_diff"]
X = pd.concat([df[feature_cols], weather_ohe], axis=1)
y = df["match_score"]

# ---- Train/test split ----
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ---- Train ----
model = RandomForestRegressor(
    n_estimators=200, max_depth=8, min_samples_leaf=5, random_state=42
)
model.fit(X_train, y_train)

# ---- Evaluate ----
preds = model.predict(X_test)
mse = mean_squared_error(y_test, preds)
r2 = r2_score(y_test, preds)
print(f"Test MSE: {mse:.4f}")
print(f"Test R^2: {r2:.4f}")

# Feature importance -- useful to show in your report/viva
importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
print("\nFeature importances:")
print(importances)

# ---- Save model + feature column order (needed at inference time) ----
joblib.dump(model, "recommender_model.pkl")
joblib.dump(list(X.columns), "feature_columns.pkl")
print("\nSaved recommender_model.pkl and feature_columns.pkl")
