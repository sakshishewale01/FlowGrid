"""
FlowGrid AI-Ready Data Pipeline Package
=======================================
Modular pipeline transforming operational database entities into leak-free,
audited datasets for future machine learning model training.
"""

from app.pipeline.schema import (
    FeatureCategory,
    FeatureDefinition,
    FEATURE_REGISTRY,
    DatasetRecord,
    DataQualityIssue,
    DataQualityReport,
)
from app.pipeline.feature_extractor import (
    ExtractedShipmentContext,
    FeatureExtractor,
    feature_extractor,
)
from app.pipeline.feature_engineer import (
    FeatureEngineer,
    feature_engineer,
)
from app.pipeline.quality_checker import (
    DataQualityChecker,
    quality_checker,
)
from app.pipeline.dataset_generator import (
    DatasetGenerator,
    dataset_generator,
)

__all__ = [
    "FeatureCategory",
    "FeatureDefinition",
    "FEATURE_REGISTRY",
    "DatasetRecord",
    "DataQualityIssue",
    "DataQualityReport",
    "ExtractedShipmentContext",
    "FeatureExtractor",
    "feature_extractor",
    "FeatureEngineer",
    "feature_engineer",
    "DataQualityChecker",
    "quality_checker",
    "DatasetGenerator",
    "dataset_generator",
]
