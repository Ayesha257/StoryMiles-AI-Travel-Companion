"""Inference support for the pre-trained destination recommender."""

from app.ml.model_loader import get_model_health, get_recommendation_artifacts, load_recommendation_artifacts

__all__ = ["get_model_health", "get_recommendation_artifacts", "load_recommendation_artifacts"]
