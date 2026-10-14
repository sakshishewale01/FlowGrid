"""
FlowGrid AI - India Delay Prediction Baseline Experiment
=========================================================
Trains and evaluates baseline shipment-delay classifiers on the staged India dataset:
`backend/ml_data/india/flowgrid_delay_model_india.csv`

Requirements satisfied:
1. Target: is_delayed (binary classification 0/1).
2. Excludes shipment_id and raw date string (extracts date features: month, day_of_week, is_weekend).
3. Preprocessing: DictVectorizer (encodes categoricals, retains numericals) with reproducible split.
4. Stratified train/test split (80/20, random_state=42).
5. Baseline comparison: DummyClassifier(strategy='most_frequent') vs. RandomForestClassifier.
6. Evaluation metrics: Confusion matrix, Precision, Recall, F1-score, ROC-AUC.
7. Saves full pipeline artifact to backend/ml/models/india_delay_pipeline.joblib and metrics.json.
8. Strictly decoupled: zero PostgreSQL interaction.

CRITICAL DATA NOTICE:
The delay labels in this dataset are carried over from synthetic benchmark data
and DO NOT establish genuine Indian freight operations or real-world delay correlations.
This model serves strictly as a prototype demonstrator.
"""

import os
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction import DictVectorizer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR.parent / "ml_data" / "india" / "flowgrid_delay_model_india.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_ARTIFACT_PATH = MODEL_DIR / "india_delay_pipeline.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"


def load_and_preprocess_data(csv_path: Path) -> Tuple[List[Dict[str, Any]], List[int]]:
    """
    Loads raw CSV data and constructs feature records without data leakage.
    Extracts calendar features from date and removes identifiers.
    """
    records: List[Dict[str, Any]] = []
    targets: List[int] = []

    with open(csv_path, mode="r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse date safely without leakage
            date_str = row["date"].strip()
            dt = datetime.strptime(date_str, "%Y-%m-%d")

            feature_dict = {
                "warehouse": row["warehouse"].strip(),
                "destination": row["destination"].strip(),
                "transport_mode": row["transport_mode"].strip(),
                "supplier": row["supplier"].strip(),
                "driver": row["driver"].strip(),
                "distance_km": float(row["distance_km"]),
                "month": float(dt.month),
                "day_of_week": float(dt.weekday()),
                "is_weekend": 1.0 if dt.weekday() >= 5 else 0.0,
            }

            # Target: is_delayed
            delayed_str = row["is_delayed"].strip().lower()
            is_delayed = 1 if delayed_str == "true" else 0

            records.append(feature_dict)
            targets.append(is_delayed)

    return records, targets


def run_experiment() -> Dict[str, Any]:
    """
    Runs train/test evaluation comparing Dummy baseline against RandomForest.
    Saves trained pipeline artifact and metrics.
    """
    print(f"Loading dataset from: {DATASET_PATH}")
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")

    X_dicts, y = load_and_preprocess_data(DATASET_PATH)
    total_samples = len(y)
    positives = sum(y)
    negatives = total_samples - positives

    print(f"Total samples: {total_samples}")
    print(f"Class balance: Not Delayed (0) = {negatives} ({negatives/total_samples*100:.2f}%), "
          f"Delayed (1) = {positives} ({positives/total_samples*100:.2f}%)")

    # Stratified Train/Test split (80/20) with fixed seed
    X_train, X_test, y_train, y_test = train_test_split(
        X_dicts,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    # 1. Baseline Model: DummyClassifier (most frequent class)
    dummy_pipeline = Pipeline([
        ("vectorizer", DictVectorizer(sparse=False)),
        ("classifier", DummyClassifier(strategy="most_frequent")),
    ])
    dummy_pipeline.fit(X_train, y_train)
    dummy_preds = dummy_pipeline.predict(X_test)
    dummy_probs = dummy_pipeline.predict_proba(X_test)[:, 1]

    # 2. Candidate Model: RandomForestClassifier with balanced class weighting
    rf_pipeline = Pipeline([
        ("vectorizer", DictVectorizer(sparse=False)),
        ("classifier", RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=42,
            class_weight="balanced",
        )),
    ])
    rf_pipeline.fit(X_train, y_train)
    rf_preds = rf_pipeline.predict(X_test)
    rf_probs = rf_pipeline.predict_proba(X_test)[:, 1]

    # Evaluate Dummy
    dummy_cm = confusion_matrix(y_test, dummy_preds).tolist()
    dummy_metrics = {
        "accuracy": float(np.mean(np.array(dummy_preds) == np.array(y_test))),
        "precision": float(precision_score(y_test, dummy_preds, zero_division=0)),
        "recall": float(recall_score(y_test, dummy_preds, zero_division=0)),
        "f1": float(f1_score(y_test, dummy_preds, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, dummy_probs)),
        "confusion_matrix": dummy_cm,
    }

    # Evaluate Candidate (Random Forest)
    rf_cm = confusion_matrix(y_test, rf_preds).tolist()
    rf_metrics = {
        "accuracy": float(np.mean(np.array(rf_preds) == np.array(y_test))),
        "precision": float(precision_score(y_test, rf_preds, zero_division=0)),
        "recall": float(recall_score(y_test, rf_preds, zero_division=0)),
        "f1": float(f1_score(y_test, rf_preds, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, rf_probs)),
        "confusion_matrix": rf_cm,
    }

    print("\n==================================================================")
    print("EXPERIMENT RESULTS: BASELINE vs CANDIDATE CLASSIFIER")
    print("==================================================================")
    print(f"Test Set Size: {len(y_test)} (On-Time: {y_test.count(0)}, Delayed: {y_test.count(1)})")
    print("\n--- BASELINE (DummyClassifier: Always Predict Majority Class 0) ---")
    print(f"Confusion Matrix [ [TN, FP], [FN, TP] ]: {dummy_cm}")
    print(f"Accuracy:  {dummy_metrics['accuracy']:.4f}")
    print(f"Precision: {dummy_metrics['precision']:.4f}")
    print(f"Recall:    {dummy_metrics['recall']:.4f}")
    print(f"F1-Score:  {dummy_metrics['f1']:.4f}")
    print(f"ROC-AUC:   {dummy_metrics['roc_auc']:.4f}")

    print("\n--- CANDIDATE (RandomForestClassifier, Depth=8, Balanced) ---")
    print(f"Confusion Matrix [ [TN, FP], [FN, TP] ]: {rf_cm}")
    print(f"Accuracy:  {rf_metrics['accuracy']:.4f}")
    print(f"Precision: {rf_metrics['precision']:.4f}")
    print(f"Recall:    {rf_metrics['recall']:.4f}")
    print(f"F1-Score:  {rf_metrics['f1']:.4f}")
    print(f"ROC-AUC:   {rf_metrics['roc_auc']:.4f}")
    print("==================================================================")

    report = {
        "experiment_timestamp": datetime.now().isoformat(),
        "dataset_path": str(DATASET_PATH),
        "total_records": total_samples,
        "train_records": len(y_train),
        "test_records": len(y_test),
        "class_distribution": {
            "on_time_0": negatives,
            "delayed_1": positives,
            "delayed_percentage": round(positives / total_samples * 100, 2),
        },
        "baseline_dummy": dummy_metrics,
        "candidate_random_forest": rf_metrics,
        "features": {
            "categorical": ["warehouse", "destination", "transport_mode", "supplier", "driver"],
            "numerical": ["distance_km", "month", "day_of_week", "is_weekend"],
            "excluded": ["shipment_id", "date", "vehicle", "route"],
        },
        "disclaimer": (
            "NOTICE: The delay labels in this dataset are carried over from synthetic benchmark data "
            "and do NOT establish genuine Indian freight operations. This model is an experimental "
            "prototype demonstrator and must not be used for real-world operational decisions."
        ),
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(rf_pipeline, MODEL_ARTIFACT_PATH)
    print(f"\nSaved trained pipeline artifact to: {MODEL_ARTIFACT_PATH}")

    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Saved evaluation metrics to: {METRICS_PATH}")

    return report


if __name__ == "__main__":
    run_experiment()
