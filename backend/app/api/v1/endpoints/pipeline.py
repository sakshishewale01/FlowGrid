"""
FlowGrid - AI-Ready Data Pipeline Endpoints
===========================================
API endpoints providing access to feature definitions, data quality reports,
ML dataset generation, and CSV exports for authorized administrators.

Permissions:
- Schema & Quality Report: ADMIN, MANAGER
- Dataset Generation & CSV Export: ADMIN, MANAGER
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.pipeline.schema import (
    FeatureDefinition,
    FEATURE_REGISTRY,
    DatasetRecord,
    DataQualityReport,
)
from app.pipeline.dataset_generator import dataset_generator

router = APIRouter()


@router.get(
    "/schema",
    response_model=List[FeatureDefinition],
    status_code=status.HTTP_200_OK,
    summary="Get AI pipeline feature registry and definitions",
    description="Returns metadata for all raw operational features, derived features, targets, and deferred IoT telemetry.",
)
def get_pipeline_schema(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER])),
) -> List[FeatureDefinition]:
    """
    Returns the comprehensive dictionary of features defined in the FlowGrid AI pipeline.
    """
    return FEATURE_REGISTRY


@router.get(
    "/quality-report",
    response_model=DataQualityReport,
    status_code=status.HTTP_200_OK,
    summary="Audit dataset quality and check for data leakage",
    description="Extracts current shipments, evaluates missing values, invalid timestamps, outliers, and verifies absence of target leakage.",
)
def get_pipeline_quality_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER])),
) -> DataQualityReport:
    """
    Runs data quality audit against current operational database records.
    """
    records = dataset_generator.generate_dataset(db, include_undelivered=True)
    return dataset_generator.audit_dataset(records)


@router.get(
    "/dataset",
    status_code=status.HTTP_200_OK,
    summary="Generate ML-ready shipment dataset",
    description="Transforms operational database records into an ML-ready dataset with optional chronological train/test splitting.",
)
def get_ml_dataset(
    include_undelivered: bool = Query(
        True,
        description="Include in-transit and active shipments alongside delivered ones",
    ),
    split: bool = Query(
        False,
        description="Whether to return a chronologically partitioned train/test split",
    ),
    train_ratio: float = Query(
        0.8,
        ge=0.1,
        le=0.95,
        description="Proportion of chronologically earlier records allocated to the training split",
    ),
    limit: Optional[int] = Query(
        None,
        gt=0,
        description="Maximum number of shipment records to process",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER])),
) -> Dict[str, Any]:
    """
    Generates and returns the engineered ML dataset.
    """
    records = dataset_generator.generate_dataset(
        db,
        include_undelivered=include_undelivered,
        limit=limit,
    )

    if split:
        train_set, test_set = dataset_generator.split_chronologically(
            records, train_ratio=train_ratio
        )
        return {
            "total_records": len(records),
            "train_ratio": train_ratio,
            "train_records_count": len(train_set),
            "test_records_count": len(test_set),
            "train": [r.model_dump() for r in train_set],
            "test": [r.model_dump() for r in test_set],
        }

    return {
        "total_records": len(records),
        "records": [r.model_dump() for r in records],
    }


@router.get(
    "/export/csv",
    status_code=status.HTTP_200_OK,
    summary="Download ML dataset as CSV",
    description="Serializes the engineered ML dataset to RFC 4180 compliant CSV format for download.",
)
def export_dataset_csv(
    include_undelivered: bool = Query(
        False,
        description="Whether to include undelivered shipments in the exported CSV",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER])),
) -> Response:
    """
    Streams CSV format of the ML dataset.
    """
    records = dataset_generator.generate_dataset(
        db,
        include_undelivered=include_undelivered,
    )
    csv_data = dataset_generator.export_to_csv(records)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=flowgrid_ml_dataset.csv",
        },
    )
