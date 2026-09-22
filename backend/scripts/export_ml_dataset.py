"""
FlowGrid - AI Dataset Export CLI Utility
========================================
CLI tool to generate, audit, chronologically split, and export FlowGrid's
operational data into ML-ready CSV and JSON files for future model training.

Usage:
------
python scripts/export_ml_dataset.py --output-dir ./ml_exports --train-ratio 0.8
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.pipeline.dataset_generator import dataset_generator


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract and export FlowGrid operational data into ML-ready datasets."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./ml_exports",
        help="Target directory where generated CSV and report files will be saved.",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Proportion of earlier records allocated to the chronological training split (default: 0.8).",
    )
    parser.add_argument(
        "--include-undelivered",
        action="store_true",
        default=False,
        help="Whether to include in-transit and active shipments alongside delivered ones.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"[*] FlowGrid AI-Ready Data Pipeline Exporter")
    print(f"[*] Connecting to database session...")

    db = SessionLocal()
    try:
        print(f"[*] Extracting and engineering features (include_undelivered={args.include_undelivered})...")
        records = dataset_generator.generate_dataset(
            db,
            include_undelivered=args.include_undelivered,
        )
        print(f"[+] Successfully extracted {len(records)} shipment records.")

        print(f"[*] Running data quality and leakage checks...")
        report = dataset_generator.audit_dataset(records)

        print(f"\n--- Data Quality Audit Summary ---")
        print(f"  Total Records:          {report.total_records}")
        print(f"  Clean Records:          {report.clean_records}")
        print(f"  Records with Targets:   {report.records_with_targets}")
        print(f"  Issues Detected:        {report.issues_count}")
        print(f"  Leakage Detected:       {report.leakage_risk_detected}")
        print(f"  Valid for ML Training:  {report.is_valid_for_training}")

        # Split chronologically
        train_set, test_set = dataset_generator.split_chronologically(
            records, train_ratio=args.train_ratio
        )
        print(f"\n[*] Chronological Partition:")
        print(f"  Training Split: {len(train_set)} records")
        print(f"  Testing Split:  {len(test_set)} records")

        # Export CSVs and Report
        train_csv_path = output_path / "train_dataset.csv"
        test_csv_path = output_path / "test_dataset.csv"
        full_csv_path = output_path / "full_dataset.csv"
        report_json_path = output_path / "data_quality_report.json"

        dataset_generator.export_to_csv(train_set, str(train_csv_path))
        dataset_generator.export_to_csv(test_set, str(test_csv_path))
        dataset_generator.export_to_csv(records, str(full_csv_path))

        with open(report_json_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        print(f"\n[+] Generated Files:")
        print(f"  Train:   {train_csv_path.resolve()}")
        print(f"  Test:    {test_csv_path.resolve()}")
        print(f"  Full:    {full_csv_path.resolve()}")
        print(f"  Report:  {report_json_path.resolve()}")
        print(f"[+] Dataset export completed successfully.\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()
