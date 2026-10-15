"""
FlowGrid - Grounded Logistics Assistant Service
================================================
Deterministic, explainable assistant grounded strictly in:
1. Live PostgreSQL records (Shipments, Warehouses, Drivers, Vehicles).
2. Existing operational rule definitions (UNASSIGNED_DRIVER, UNASSIGNED_VEHICLE, etc.).
3. ML prototype transparency disclosures (ROC-AUC 0.5062 synthetic benchmark disclaimer).
4. Non-destructive What-If Disruption Simulator documentation.

Security & Integrity Guarantees:
- Enforces user RBAC boundaries.
- Read-only execution: Zero database mutations, zero arbitrary SQL, zero shell calls.
- Never invents missing records, statuses, drivers, locations, or external weather/traffic.
"""

import re
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.models.shipment import Shipment, ShipmentStatus
from app.services.delay_risk_service import delay_risk_service
from app.schemas.assistant import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    AssistantSource,
)


class AssistantService:
    """
    Coordinates grounded question answering across FlowGrid's authenticated services.
    """

    def process_query(
        self,
        db: Session,
        current_user: User,
        request: AssistantQueryRequest,
    ) -> AssistantQueryResponse:
        query_text = request.query.strip()
        query_lower = query_text.lower()
        now_iso = datetime.now(timezone.utc).isoformat()

        # ----------------------------------------------------------------------
        # 1. Intent: Shipment Status Query
        # ----------------------------------------------------------------------
        if self._is_shipment_status_query(query_lower):
            return self._handle_shipment_status(db, current_user, query_text, query_lower, now_iso)

        # ----------------------------------------------------------------------
        # 2. Intent: Attention-Worthy Shipments
        # ----------------------------------------------------------------------
        if any(k in query_lower for k in ("need attention", "needs attention", "attention-worthy", "which shipments", "bottleneck", "at risk", "at-risk")):
            return self._handle_attention_shipments(db, current_user, query_text, now_iso)

        # ----------------------------------------------------------------------
        # 3. Intent: Rescue Center Workflow Explanation
        # ----------------------------------------------------------------------
        if any(k in query_lower for k in ("rescue center", "how do i use", "how to use", "triage", "rescue")):
            return self._handle_rescue_center_workflow(query_text, now_iso)

        # ----------------------------------------------------------------------
        # 4. Intent: Delay Prediction Model Meaning & Transparency
        # ----------------------------------------------------------------------
        if any(k in query_lower for k in ("delay prediction", "random forest", "ml model", "machine learning", "roc-auc", "predict-delay")):
            return self._handle_delay_prediction_meaning(query_text, now_iso)

        # ----------------------------------------------------------------------
        # 5. Intent: What-If Disruption Simulator Explanation
        # ----------------------------------------------------------------------
        if any(k in query_lower for k in ("simulator", "what-if", "what if", "disruption", "sandbox", "scenario")):
            return self._handle_simulator_explanation(query_text, now_iso)

        # ----------------------------------------------------------------------
        # 6. Intent: Help & Overview
        # ----------------------------------------------------------------------
        if re.search(r"\b(help|what can you do|capabilities|hello|hi|hey)\b", query_lower):
            return self._handle_general_help(query_text, now_iso)

        # ----------------------------------------------------------------------
        # 7. Unsupported / External Query Refusal
        # ----------------------------------------------------------------------
        return self._handle_unsupported_query(query_text, now_iso)

    # --------------------------------------------------------------------------
    # Intent Handlers
    # --------------------------------------------------------------------------

    def _is_shipment_status_query(self, query_lower: str) -> bool:
        status_keywords = ("status of shipment", "where is shipment", "track shipment", "shipment status")
        has_status_kw = any(k in query_lower for k in status_keywords)
        has_id_pattern = bool(re.search(r"\bshipment\s+#?\d+\b", query_lower) or re.search(r"\bfg-[\w-]+\b", query_lower))
        return has_status_kw or has_id_pattern

    def _handle_shipment_status(
        self,
        db: Session,
        current_user: User,
        query: str,
        query_lower: str,
        now_iso: str,
    ) -> AssistantQueryResponse:
        # Extract potential shipment ID or tracking number
        id_match = re.search(r"\bshipment\s+#?(\d+)\b", query_lower)
        if not id_match:
            id_match = re.search(r"\b#?(\d+)\b", query_lower)
        tracking_match = re.search(r"\b(fg-[\w-]+)\b", query_lower)

        shipment = None
        shipment_identifier = None

        if id_match:
            shipment_id = int(id_match.group(1))
            shipment_identifier = f"#{shipment_id}"
            shipment = (
                db.query(Shipment)
                .options(
                    joinedload(Shipment.origin_warehouse),
                    joinedload(Shipment.assigned_driver),
                    joinedload(Shipment.assigned_vehicle),
                    joinedload(Shipment.routes),
                )
                .filter(Shipment.id == shipment_id)
                .first()
            )
        elif tracking_match:
            tracking_num = tracking_match.group(1).upper()
            shipment_identifier = tracking_num
            shipment = (
                db.query(Shipment)
                .options(
                    joinedload(Shipment.origin_warehouse),
                    joinedload(Shipment.assigned_driver),
                    joinedload(Shipment.assigned_vehicle),
                    joinedload(Shipment.routes),
                )
                .filter(Shipment.tracking_number == tracking_num)
                .first()
            )

        # Case 1: Specific shipment found
        if shipment:
            # RBAC Enforcement: If DRIVER, ensure driver is assigned to this shipment
            if current_user.role == UserRole.DRIVER:
                driver_profile = current_user.driver
                if not driver_profile or shipment.assigned_driver_id != driver_profile.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: Drivers may only query telemetry for their own assigned shipments.",
                    )

            # Evaluate delay risk for grounded metrics
            risk_eval = delay_risk_service.evaluate_shipment(shipment)
            driver_name = shipment.assigned_driver.user.name if shipment.assigned_driver and shipment.assigned_driver.user else ("Assigned" if shipment.assigned_driver_id else "Unassigned")
            vehicle_reg = shipment.assigned_vehicle.registration_number if shipment.assigned_vehicle else "Unassigned"
            origin_name = shipment.origin_warehouse.name if shipment.origin_warehouse else "Origin Hub"
            weight_str = f"{float(shipment.total_weight_kg):,.1f} kg" if shipment.total_weight_kg else "Payload unstated"

            answer = (
                f"**Shipment Status Report for Waybill {shipment.tracking_number} (ID #{shipment.id}):**\n\n"
                f"• **Current Operational Lifecycle State:** `{shipment.status.value}`\n"
                f"• **Corridor Origin & Destination:** {origin_name} → {shipment.destination_city}, {shipment.destination_state}\n"
                f"• **Consignee Address:** {shipment.destination_address}, {shipment.destination_postal_code}\n"
                f"• **Cargo Payload:** {weight_str}\n"
                f"• **Assigned Driver:** {driver_name}\n"
                f"• **Assigned Transport Unit:** {vehicle_reg}\n"
                f"• **Deterministic Operational Delay Risk Score:** {risk_eval.risk_score} / 100 ({risk_eval.risk_category})\n\n"
                f"**Explanation:** {risk_eval.summary_explanation}"
            )

            sources = [
                AssistantSource(
                    source_type="RETRIEVED_FACT",
                    title=f"PostgreSQL Operational Table: Shipments (ID #{shipment.id})",
                    content=f"Tracking: {shipment.tracking_number}, Status: {shipment.status.value}, Origin: {origin_name}, Destination: {shipment.destination_city}, {shipment.destination_state}",
                    reference_id=str(shipment.id),
                ),
                AssistantSource(
                    source_type="OPERATIONAL_RULE",
                    title="Deterministic Delay Risk Scoring Engine",
                    content=f"Score: {risk_eval.risk_score}/100, Tier: {risk_eval.risk_category}, Factors: {len(risk_eval.contributing_factors)} active contributor(s)",
                    reference_id="DELAY_RISK_HEURISTIC",
                ),
            ]

            return AssistantQueryResponse(
                query=query,
                intent="SHIPMENT_STATUS",
                answer=answer,
                sources=sources,
                suggested_chips=[
                    "Which shipments need attention according to the available data?",
                    "How do I use the Shipment Rescue Center?",
                    "What does the delay prediction mean?",
                ],
                timestamp=now_iso,
            )

        # Case 2: Specific ID queried, but not in database -> REFUSE TO INVENT
        if shipment_identifier:
            real_shipments = db.query(Shipment).filter(Shipment.is_active.is_(True)).order_by(Shipment.id.asc()).limit(5).all()
            available_examples = ", ".join([f"ID #{s.id} ({s.tracking_number})" for s in real_shipments]) if real_shipments else "No active shipments currently exist."

            answer = (
                f"⚠️ **Record Unavailable:** Shipment '{shipment_identifier}' was not found in the FlowGrid PostgreSQL database.\n\n"
                f"FlowGrid operates under strict data integrity standards and **refuses to invent or hallucinate shipment records**.\n\n"
                f"Currently available active shipments in your system include: {available_examples}.\n\n"
                f"Please verify the tracking waybill or query one of the existing IDs above."
            )

            return AssistantQueryResponse(
                query=query,
                intent="SHIPMENT_STATUS",
                answer=answer,
                sources=[
                    AssistantSource(
                        source_type="SYSTEM_GUIDANCE",
                        title="Data Integrity & Hallucination Prevention Policy",
                        content="Unverified shipment IDs are rejected. No synthetic statuses or coordinates are fabricated.",
                    )
                ],
                suggested_chips=[
                    f"What is the status of shipment {real_shipments[0].id}?" if real_shipments else "Which shipments need attention according to the available data?",
                    "How do I use the Shipment Rescue Center?",
                    "What does the delay prediction mean?",
                ],
                timestamp=now_iso,
            )

        # Case 3: No specific ID provided in query -> Prompt with real available IDs
        real_shipments = db.query(Shipment).filter(Shipment.is_active.is_(True)).order_by(Shipment.id.asc()).limit(5).all()
        options_text = "\n".join([f"• **Shipment #{s.id}:** {s.tracking_number} ({s.status.value}) — {s.destination_city}, {s.destination_state}" for s in real_shipments])

        answer = (
            f"Please specify a shipment ID or tracking number to query telemetry.\n\n"
            f"**Currently Available Shipments in Your Control Tower:**\n"
            f"{options_text}\n\n"
            f"Try asking: *\"What is the status of shipment {real_shipments[0].id if real_shipments else 1}?\"*"
        )

        return AssistantQueryResponse(
            query=query,
            intent="SHIPMENT_STATUS",
            answer=answer,
            sources=[
                AssistantSource(
                    source_type="RETRIEVED_FACT",
                    title="Active Operational Manifests",
                    content=f"Retrieved {len(real_shipments)} active shipment records from PostgreSQL database.",
                )
            ],
            suggested_chips=[
                f"What is the status of shipment {real_shipments[0].id}?" if real_shipments else "Which shipments need attention according to the available data?",
                "Which shipments need attention according to the available data?",
                "How does the What-If Disruption Simulator work?",
            ],
            timestamp=now_iso,
        )

    def _handle_attention_shipments(
        self,
        db: Session,
        current_user: User,
        query: str,
        now_iso: str,
    ) -> AssistantQueryResponse:
        # Retrieve active shipments
        query_set = (
            db.query(Shipment)
            .options(
                joinedload(Shipment.origin_warehouse),
                joinedload(Shipment.assigned_driver),
                joinedload(Shipment.assigned_vehicle),
                joinedload(Shipment.routes),
            )
            .filter(Shipment.is_active.is_(True))
            .filter(~Shipment.status.in_([ShipmentStatus.DELIVERED, ShipmentStatus.CANCELLED, ShipmentStatus.RETURNED]))
            .order_by(Shipment.id.asc())
        )

        # RBAC: Drivers only see their own assigned shipments
        if current_user.role == UserRole.DRIVER:
            driver_profile = current_user.driver
            driver_id = driver_profile.id if driver_profile else -1
            query_set = query_set.filter(Shipment.assigned_driver_id == driver_id)

        shipments = query_set.all()

        attention_items = []
        sources = []

        for s in shipments:
            eval_res = delay_risk_service.evaluate_shipment(s)
            reasons = []

            if not s.assigned_driver_id:
                reasons.append("Unassigned Driver (`[RULE-R01]`, +20 pts)")
            if not s.assigned_vehicle_id:
                reasons.append("Unassigned Equipment (`[RULE-R02]`, +15 pts)")
            if not eval_res.has_route_assigned:
                reasons.append("Unassigned Corridor (`[RULE-R03]`, +10 pts)")
            if s.status == ShipmentStatus.FAILED:
                reasons.append("Dispatch / Transit Exception (`[RULE-EX01]`)")
            if eval_res.weight_capacity_utilization and eval_res.weight_capacity_utilization > 0.85:
                reasons.append(f"Capacity Load Strain ({eval_res.weight_capacity_utilization * 100:.1f}%)")

            if reasons or eval_res.risk_score >= 40:
                attention_items.append({
                    "shipment": s,
                    "score": eval_res.risk_score,
                    "tier": eval_res.risk_category,
                    "reasons": reasons,
                })
                sources.append(
                    AssistantSource(
                        source_type="OPERATIONAL_RULE",
                        title=f"Attention Flag: Shipment #{s.id} ({s.tracking_number})",
                        content=f"Risk Score: {eval_res.risk_score}/100. Factors: {', '.join(reasons)}",
                        reference_id=str(s.id),
                    )
                )

        if attention_items:
            lines = [f"**Found {len(attention_items)} active shipment(s) requiring operational attention:**\n"]
            for item in attention_items:
                s = item["shipment"]
                reasons_str = "; ".join(item["reasons"]) if item["reasons"] else "Elevated transit corridor variance"
                lines.append(
                    f"• **Waybill {s.tracking_number} (ID #{s.id}):**\n"
                    f"  - **Status:** `{s.status.value}` | **Corridor:** {s.origin_warehouse.name if s.origin_warehouse else 'Origin Hub'} → {s.destination_city}, {s.destination_state}\n"
                    f"  - **Delay Risk Score:** **{item['score']}/100** ({item['tier']})\n"
                    f"  - **Triggered Rules:** {reasons_str}\n"
                )
            lines.append("💡 **Recommended Next Step:** Open the **Shipment Rescue Center** to review recommendations and allocate available standby assets with human confirmation.")
            answer = "\n".join(lines)
        else:
            answer = (
                "✓ **Zero Bottlenecks Detected:** All monitored shipments currently have complete driver, vehicle, and corridor allocations, and operate within standard risk parameters.\n\n"
                "You can inspect live fleet throughput and corridors in the **Shipments** or **Analytics** page."
            )

        return AssistantQueryResponse(
            query=query,
            intent="ATTENTION_SHIPMENTS",
            answer=answer,
            sources=sources,
            suggested_chips=[
                "How do I use the Shipment Rescue Center?",
                "What does the delay prediction mean?",
                "How does the What-If Disruption Simulator work?",
            ],
            timestamp=now_iso,
        )

    def _handle_rescue_center_workflow(self, query: str, now_iso: str) -> AssistantQueryResponse:
        answer = (
            "### 🛡️ How to Use the Shipment Rescue Center\n\n"
            "The **Shipment Rescue Center** serves as FlowGrid's primary operational triage hub for identifying and resolving freight bottlenecks. It follows a four-stage workflow:\n\n"
            "1. **DETECT:**\n"
            "   - Scans live PostgreSQL shipments and flags manifests missing key assets:\n"
            "     - `[RULE-R01] Unassigned Driver` (+20 delay risk pts)\n"
            "     - `[RULE-R02] Unassigned Equipment` (+15 delay risk pts)\n"
            "     - `[RULE-R03] Unassigned Route Corridor` (+10 delay risk pts)\n"
            "     - `[RULE-R04] Vehicle Capacity Strain (>85%)` (+10 to +20 pts)\n"
            "     - `[RULE-EX01] Dispatch / Transit Exception (FAILED)`\n\n"
            "2. **RECOMMEND:**\n"
            "   - The **Operational Recommendations Engine** matches unallocated manifests with verified standby drivers (`AVAILABLE`) and transport vehicles with sufficient cargo payload capacity.\n\n"
            "3. **HUMAN CONFIRMATION GATE:**\n"
            "   - No changes occur autonomously. Clicking **\"Review & Apply\"** prompts a confirmation dialog displaying the exact database IDs before persisting mutations to PostgreSQL.\n\n"
            "4. **PREDICT (OPTIONAL ML):**\n"
            "   - Operators can launch the **Random Forest ML Predictor** modal to evaluate transit corridor delay probabilities against the India freight benchmark."
        )

        sources = [
            AssistantSource(
                source_type="OPERATIONAL_RULE",
                title="FlowGrid Control Tower Triage Rules",
                content="Rules R01-R05 provide explainable operational heuristics based strictly on database fields.",
                reference_id="RESCUE_CENTER_WORKFLOW",
            )
        ]

        return AssistantQueryResponse(
            query=query,
            intent="RESCUE_CENTER_WORKFLOW",
            answer=answer,
            sources=sources,
            suggested_chips=[
                "Which shipments need attention according to the available data?",
                "What does the delay prediction mean?",
                "How does the What-If Disruption Simulator work?",
            ],
            timestamp=now_iso,
        )

    def _handle_delay_prediction_meaning(self, query: str, now_iso: str) -> AssistantQueryResponse:
        answer = (
            "### 🤖 Understanding FlowGrid's Delay Risk Models\n\n"
            "FlowGrid maintains an explicit distinction between its two delay evaluation systems:\n\n"
            "1. **⚙️ Deterministic Operational Heuristics (0–100 Score):**\n"
            "   - Calculated directly from real database attributes (e.g. unassigned driver +20, unassigned vehicle +15, unassigned corridor +10, capacity load >90% +20, interstate corridor +15).\n"
            "   - This is an **explainable operational rule index**, NOT an empirical probability.\n\n"
            "2. **✦ India Corridor Delay ML Model (`POST /api/v1/ml/predict-delay`):**\n"
            "   - A saved scikit-learn Random Forest classifier and preprocessing pipeline (`india_delay_pipeline.joblib`).\n"
            "   - Trained on the India logistics benchmark dataset (1,451 records) using features: origin warehouse, destination hub, vehicle classification, distance km, carrier partner, and driver alias.\n\n"
            "⚠️ **Mandatory Prototype Disclosure:**\n"
            "The Random Forest model has a reported **ROC-AUC of 0.5062 on synthetic benchmark data**. It is **NOT validated for real-world operational decisions** and does not predict genuine live carrier outcomes. It is provided strictly to demonstrate model serving, feature serialization, and decoupled inference architecture."
        )

        sources = [
            AssistantSource(
                source_type="ML_DISCLAIMER",
                title="Random Forest Classifier Prototype Disclosure",
                content="ROC-AUC 0.5062 on synthetic India logistics benchmark data. Not calibrated for real-world production decisions.",
                reference_id="ML_SYNTHETIC_BENCHMARK",
            ),
            AssistantSource(
                source_type="OPERATIONAL_RULE",
                title="Operational Heuristic Scoring Engine",
                content="Deterministic 0-100 scoring based on verified database allocation fields.",
                reference_id="HEURISTIC_RULES",
            ),
        ]

        return AssistantQueryResponse(
            query=query,
            intent="DELAY_PREDICTION_MEANING",
            answer=answer,
            sources=sources,
            suggested_chips=[
                "How do I use the Shipment Rescue Center?",
                "Which shipments need attention according to the available data?",
                "How does the What-If Disruption Simulator work?",
            ],
            timestamp=now_iso,
        )

    def _handle_simulator_explanation(self, query: str, now_iso: str) -> AssistantQueryResponse:
        answer = (
            "### ⚡ What-If Disruption Simulator Architecture\n\n"
            "The **What-If Disruption Simulator** allows logistics dispatchers to test contingency plans before disruptions strike, using a completely safe sandbox environment:\n\n"
            "• **100% Non-Destructive Sandbox:**\n"
            "  - All calculations execute in volatile client memory.\n"
            "  - **Zero PostgreSQL mutations:** Real shipments, warehouse inventories, driver assignments, and vehicle statuses are never altered.\n\n"
            "• **Scenario 1: Warehouse Facility Outage & Rerouting:**\n"
            "  - Select an active origin facility (e.g. Chicago ORD-01) and model events like conveyor breakdowns (12h) or blizzard shutdowns (36h).\n"
            "  - Evaluates diversion to partner hubs (e.g. Newark EWR-02), computing target hub capacity influx (`Target Load %`) and detour transit penalties.\n\n"
            "• **Scenario 2: Highway Corridor Disruption:**\n"
            "  - Select an active shipment and model highway closures (+8h) or vehicle breakdowns (+14h).\n"
            "  - Tests recovery strategies like hot-swap standby units or secondary highway bypasses, verifying real-time standby availability of fleet assets.\n\n"
            "• **Transparent Arithmetic:**\n"
            "  - `Mitigated Delay = max(0, Disruption Duration − Recovery Action Offset)`\n"
            "  - `Target Load % = min(100, (Diverted Payload / Target Facility Capacity) × 100)`"
        )

        sources = [
            AssistantSource(
                source_type="SIMULATOR_SANDBOX",
                title="Non-Destructive What-If Simulation Sandbox",
                content="Hypothetical modeling with zero side-effects on PostgreSQL database tables.",
                reference_id="SIMULATOR_SANDBOX",
            )
        ]

        return AssistantQueryResponse(
            query=query,
            intent="DISRUPTION_SIMULATOR",
            answer=answer,
            sources=sources,
            suggested_chips=[
                "How do I use the Shipment Rescue Center?",
                "Which shipments need attention according to the available data?",
                "What does the delay prediction mean?",
            ],
            timestamp=now_iso,
        )

    def _handle_general_help(self, query: str, now_iso: str) -> AssistantQueryResponse:
        answer = (
            "👋 **Hello! I am the FlowGrid Grounded Logistics Assistant.**\n\n"
            "I help operators navigate the control tower, inspect live shipments, and review deterministic delay risk models grounded strictly in authenticated database records.\n\n"
            "**Supported Questions:**\n"
            "1. *\"How do I use the Shipment Rescue Center?\"*\n"
            "2. *\"What is the status of shipment [ID]?\"*\n"
            "3. *\"Which shipments need attention according to the available data?\"*\n"
            "4. *\"What does the delay prediction mean?\"*\n"
            "5. *\"How does the What-If Disruption Simulator work?\"*\n\n"
            "🛡️ **Integrity Guarantee:** I do not invent fake shipments, driver locations, weather signals, or arbitrary numbers."
        )

        return AssistantQueryResponse(
            query=query,
            intent="HELP",
            answer=answer,
            sources=[
                AssistantSource(
                    source_type="SYSTEM_GUIDANCE",
                    title="FlowGrid Grounded Control Tower Assistant",
                    content="Deterministic intent-based logistics intelligence assistant.",
                )
            ],
            suggested_chips=[
                "How do I use the Shipment Rescue Center?",
                "Which shipments need attention according to the available data?",
                "What does the delay prediction mean?",
                "How does the What-If Disruption Simulator work?",
            ],
            timestamp=now_iso,
        )

    def _handle_unsupported_query(self, query: str, now_iso: str) -> AssistantQueryResponse:
        answer = (
            "⚠️ **Query Outside Operational Scope:**\n\n"
            "I am the FlowGrid Grounded Logistics Assistant. I answer questions grounded strictly in verified application workflows and active database records.\n\n"
            "I **refuse to hallucinate or guess** external information such as live consumer weather forecasts, general web knowledge, or ungrounded predictions.\n\n"
            "Please select one of the supported operational questions below to query live telemetry or application guidance."
        )

        return AssistantQueryResponse(
            query=query,
            intent="UNSUPPORTED",
            answer=answer,
            sources=[
                AssistantSource(
                    source_type="SYSTEM_GUIDANCE",
                    title="Hallucination Prevention Policy",
                    content="Refusal to generate ungrounded external claims or unverified metrics.",
                )
            ],
            suggested_chips=[
                "How do I use the Shipment Rescue Center?",
                "Which shipments need attention according to the available data?",
                "What does the delay prediction mean?",
                "How does the What-If Disruption Simulator work?",
            ],
            timestamp=now_iso,
        )


# Singleton assistant instance
assistant_service = AssistantService()
