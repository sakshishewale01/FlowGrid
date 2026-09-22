"""
FlowGrid - AI Pipeline Dataset Generator
========================================
Coordinates end-to-end extraction, feature engineering, quality auditing,
chronological train/test splitting, and serialization to CSV and JSON formats.
"""

import csv
import io
import json
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session

from app.pipeline.schema import DatasetRecord, DataQualityReport
from app.pipeline.feature_extractor import feature_extractor
from app.pipeline.feature_engineer import feature_engineer
from app.pipeline.quality_checker import quality_checker


class DatasetGenerator:
    """
    Orchestrates dataset creation, chronological splitting, and artifact exports.
    """

    def __init__(
        self,
        extractor=feature_extractor,
        engineer=feature_engineer,
        checker=quality_checker,
    ):
        self.extractor = extractor
        self.engineer = engineer
        self.checker = checker

    def generate_dataset(
        self,
        db: Session,
        include_undelivered: bool = True,
        limit: Optional[int] = None,
    ) -> List[DatasetRecord]:
        """
        Extracts operational entities and engineers features into a collection of DatasetRecords.
        """
        contexts = self.extractor.extract_all_shipments(
            db,
            include_undelivered=include_undelivered,
            limit=limit,
        )
        return [self.engineer.transform(ctx) for ctx in contexts]

    def audit_dataset(self, records: List[DatasetRecord]) -> DataQualityReport:
        """
        Executes data quality checks and leakage validation against dataset records.
        """
        return self.checker.audit(records)

    def split_chronologically(
        self,
        records: List[DatasetRecord],
        train_ratio: float = 0.8,
    ) -> Tuple[List[DatasetRecord], List[DatasetRecord]]:
        """
        Splits dataset chronologically based on shipment created/pickup timestamp
        to strictly prevent future temporal leakage into training data.
        """
        if not records:
            return [], []

        if not (0.0 < train_ratio < 1.0):
            raise ValueError(f"train_ratio must be between 0.0 and 1.0, received {train_ratio}")

        # Deterministic chronological sort using ISO timestamp strings
        sorted_records = sorted(
            records,
            key=lambda r: r.scheduled_pickup_timestamp or r.created_timestamp,
        )

        split_idx = int(len(sorted_records) * train_ratio)
        # Ensure at least 1 record in train set if records exist
        if split_idx == 0 and len(sorted_records) > 1:
            split_idx = 1

        train_set = sorted_records[:split_idx]
        test_set = sorted_records[split_idx:]

        return train_set, test_set

    def export_to_csv(
        self,
        records: List[DatasetRecord],
        filepath: Optional[str] = None,
    ) -> str:
        """
        Serializes dataset records into RFC 4180 compliant CSV format.
        """
        if not records:
            output = io.StringIO()
            writer = csv.writer(output)
            # Use schema fields if records list is empty
            fieldnames = list(DatasetRecord.model_fields.keys())
            writer.writerow(fieldnames)
            csv_content = output.getvalue()
            if filepath:
                with open(filepath, "w", newline="", encoding="utf-8") as f:
                    f.write(csv_content)
            return csv_content

        output = io.StringIO()
        fieldnames = list(records[0].model_dump().keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(r.model_dump())

        csv_content = output.getvalue()
        if filepath:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                f.write(csv_content)

        return csv_content

    def export_to_json(
        self,
        records: List[DatasetRecord],
        filepath: Optional[str] = None,
        indent: int = 2,
    ) -> str:
        """
        Serializes dataset records into JSON format.
        """
        data = [r.model_dump() for r in records]
        json_content = json.dumps(data, indent=indent)
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(json_content)
        return json_content


dataset_generator = DatasetGenerator()
