"""
FlowGrid AI - Grounded Logistics Assistant Endpoints
===================================================
Provides authenticated natural language querying grounded in live database telemetry,
operational delay-risk heuristics, and verified workflow documentation.

Permissions:
- Accessible to all authenticated users (ADMIN, MANAGER, DRIVER, VIEWER).
- Unauthenticated requests are rejected with HTTP 401 Unauthorized.
- Drivers are restricted to querying their own assigned manifests (RBAC enforced).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.assistant import AssistantQueryRequest, AssistantQueryResponse
from app.services.assistant_service import assistant_service

router = APIRouter()


@router.post(
    "/query",
    response_model=AssistantQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query the Grounded Logistics Assistant",
    description=(
        "Processes authenticated operator questions grounded strictly in live PostgreSQL records, "
        "operational heuristic rules, and verified application workflows. "
        "Strictly read-only: Zero database mutations, zero hallucinated facts."
    ),
)
def query_assistant(
    request: AssistantQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssistantQueryResponse:
    """
    Evaluates operator query and returns structured, grounded answers backed by real database records.
    """
    return assistant_service.process_query(db, current_user, request)
