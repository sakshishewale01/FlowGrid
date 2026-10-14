"""
FlowGrid AI - Machine Learning Prediction Endpoints
===================================================
Provides real-time shipment delay classification and risk scoring endpoints.

Permissions:
- Accessible to all authenticated users (ADMIN, MANAGER, DRIVER, VIEWER).
- Unauthenticated requests are rejected with HTTP 401 Unauthorized.
"""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.ml import DelayPredictionRequest, DelayPredictionResponse
from app.services.ml_service import ml_delay_service

router = APIRouter()


@router.post(
    "/predict-delay",
    response_model=DelayPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict shipment delay risk",
    description=(
        "Executes machine learning inference to predict delay risk for given freight corridor features. "
        "Strictly decoupled: does NOT create or alter records in the PostgreSQL database. "
        "Returns prediction probability, qualitative risk level, and synthetic benchmark disclaimer."
    ),
)
def predict_shipment_delay(
    payload: DelayPredictionRequest,
    current_user: User = Depends(get_current_user),
) -> DelayPredictionResponse:
    """
    Evaluates delay probability and predicted outcome for a shipment dispatch profile.
    """
    return ml_delay_service.predict_delay(payload)
