"""
FlowGrid - AI Pipeline Data Quality Checker
===========================================
Audits dataset records for missing values, invalid timestamps, impossible durations,
extreme outliers, duplicate records, and data leakage risks.
"""

from collections import Counter
from datetime import datetime
from typing import List

from app.pipeline.schema import DatasetRecord, DataQualityIssue, DataQualityReport


class DataQualityChecker:
    """
    Validates ML readiness, schema compliance, and data leakage prevention.
    """

    @staticmethod
    def audit(records: List[DatasetRecord]) -> DataQualityReport:
        """
        Runs comprehensive validation rules against a collection of DatasetRecords.
        """
        report = DataQualityReport(
            total_records=len(records),
            clean_records=0,
            records_with_targets=0,
            missing_values_by_column={},
            issues_count=0,
            issues=[],
            leakage_risk_detected=False,
            is_valid_for_training=True,
        )

        if not records:
            report.is_valid_for_training = False
            return report

        # Initialize missing values counter
        first_record_dict = records[0].model_dump()
        for col in first_record_dict.keys():
            report.missing_values_by_column[col] = 0

        id_counts = Counter(r.shipment_id for r in records)
        seen_duplicate_logged = set()
        clean_count = 0

        for r in records:
            has_record_error = False
            rec_dict = r.model_dump()

            # 1. Missing values aggregation
            for col, val in rec_dict.items():
                if val is None or val == "":
                    report.missing_values_by_column[col] += 1

            # 2. Duplicate shipment check
            if id_counts[r.shipment_id] > 1:
                has_record_error = True
                if r.shipment_id not in seen_duplicate_logged:
                    seen_duplicate_logged.add(r.shipment_id)
                    report.issues.append(
                        DataQualityIssue(
                            issue_type="DUPLICATE_RECORD",
                            severity="ERROR",
                            field_name="shipment_id",
                            record_id=r.shipment_id,
                            details=f"Duplicate shipment record found with ID {r.shipment_id} (occurs {id_counts[r.shipment_id]} times)",
                        )
                    )

            # 3. Non-negative / range bounds
            if r.cargo_weight_kg is not None:
                if r.cargo_weight_kg <= 0 or r.cargo_weight_kg > 100000:
                    has_record_error = True
                    report.issues.append(
                        DataQualityIssue(
                            issue_type="INVALID_NUMERICAL_VALUE",
                            severity="ERROR",
                            field_name="cargo_weight_kg",
                            record_id=r.shipment_id,
                            details=f"Weight ({r.cargo_weight_kg} kg) must be > 0 and <= 100,000 kg",
                        )
                    )

            if r.cargo_volume_cbm is not None:
                if r.cargo_volume_cbm <= 0 or r.cargo_volume_cbm > 1000:
                    has_record_error = True
                    report.issues.append(
                        DataQualityIssue(
                            issue_type="INVALID_NUMERICAL_VALUE",
                            severity="ERROR",
                            field_name="cargo_volume_cbm",
                            record_id=r.shipment_id,
                            details=f"Volume ({r.cargo_volume_cbm} cbm) must be > 0 and <= 1,000 cbm",
                        )
                    )

            if r.vehicle_capacity_kg is not None:
                if r.vehicle_capacity_kg <= 0 or r.vehicle_capacity_kg > 150000:
                    has_record_error = True
                    report.issues.append(
                        DataQualityIssue(
                            issue_type="INVALID_NUMERICAL_VALUE",
                            severity="ERROR",
                            field_name="vehicle_capacity_kg",
                            record_id=r.shipment_id,
                            details=f"Vehicle capacity ({r.vehicle_capacity_kg} kg) out of bounds",
                        )
                    )

            # 4. Timestamp integrity & inversion
            if r.actual_pickup_timestamp and r.actual_delivery_timestamp:
                try:
                    p_dt = datetime.fromisoformat(r.actual_pickup_timestamp)
                    d_dt = datetime.fromisoformat(r.actual_delivery_timestamp)
                    if d_dt < p_dt:
                        has_record_error = True
                        report.issues.append(
                            DataQualityIssue(
                                issue_type="INVALID_TIMESTAMP",
                                severity="ERROR",
                                field_name="actual_delivery_timestamp",
                                record_id=r.shipment_id,
                                details=f"Delivery timestamp ({d_dt}) precedes pickup timestamp ({p_dt})",
                            )
                        )
                except Exception as e:
                    has_record_error = True
                    report.issues.append(
                        DataQualityIssue(
                            issue_type="INVALID_TIMESTAMP",
                            severity="ERROR",
                            field_name="timestamps",
                            record_id=r.shipment_id,
                            details=f"Timestamp parsing error: {e}",
                        )
                    )

            # 5. Plausible duration check
            if r.actual_duration_hours is not None:
                if r.actual_duration_hours <= 0:
                    has_record_error = True
                    report.issues.append(
                        DataQualityIssue(
                            issue_type="IMPOSSIBLE_DURATION",
                            severity="ERROR",
                            field_name="actual_duration_hours",
                            record_id=r.shipment_id,
                            details=f"Duration ({r.actual_duration_hours} hrs) must be greater than 0",
                        )
                    )
                elif r.actual_duration_hours > 720:  # > 30 days
                    report.issues.append(
                        DataQualityIssue(
                            issue_type="OUTLIER",
                            severity="WARNING",
                            field_name="actual_duration_hours",
                            record_id=r.shipment_id,
                            details=f"Duration ({r.actual_duration_hours} hrs) exceeds 30 days; verify operational delay",
                        )
                    )

            # 6. Data leakage audit
            if r.shipment_status != "DELIVERED":
                # Undelivered shipments MUST NOT have supervised delivery targets
                if (
                    r.actual_duration_hours is not None
                    or r.is_delayed is not None
                    or r.delay_hours is not None
                ):
                    report.leakage_risk_detected = True
                    has_record_error = True
                    report.issues.append(
                        DataQualityIssue(
                            issue_type="LEAKAGE_RISK",
                            severity="ERROR",
                            field_name="targets",
                            record_id=r.shipment_id,
                            details=f"Undelivered shipment (status '{r.shipment_status}') has populated target labels",
                        )
                    )
            else:
                if r.actual_duration_hours is not None:
                    report.records_with_targets += 1

            if not has_record_error:
                clean_count += 1

        report.clean_records = clean_count
        report.issues_count = len(report.issues)

        # Dataset training validity verdict
        has_critical_errors = any(i.severity == "ERROR" for i in report.issues)
        report.is_valid_for_training = (
            not report.leakage_risk_detected
            and not has_critical_errors
            and report.records_with_targets > 0
        )

        return report


quality_checker = DataQualityChecker()
