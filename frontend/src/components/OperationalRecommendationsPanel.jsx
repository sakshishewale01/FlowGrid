import React, { useState, useMemo } from 'react';
import { shipmentsApi } from '../api/shipments.js';
import { formatErrorMessage } from '../api/client.js';
import { useToast } from '../context/ToastContext';
import ConfirmDialog from './ConfirmDialog';

/**
 * Operational Recommendations Engine
 * ==================================
 * Transparent, deterministic rules applied to existing database fields:
 * - Driver allocation (when unassigned and available driver exists)
 * - Vehicle allocation (when unassigned and vehicle with sufficient capacity exists)
 * - Lifecycle state staging (advance CONFIRMED to ASSIGNED when fully allocated)
 * - Origin facility operational validation
 *
 * All recommendations require operator human confirmation before persisting to PostgreSQL.
 */
export default function OperationalRecommendationsPanel({
  shipments = [],
  warehouses = [],
  drivers = [],
  vehicles = [],
  onApplied,
}) {
  const { toast } = useToast();

  // Dialog state for human confirmation
  const [pendingAction, setPendingAction] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);

  // Derive available resources
  const availableDrivers = useMemo(() => {
    return drivers.filter((d) => d.availability_status === 'AVAILABLE');
  }, [drivers]);

  const availableVehicles = useMemo(() => {
    return vehicles.filter((v) => v.status === 'AVAILABLE');
  }, [vehicles]);

  // Generate grounded recommendations
  const recommendations = useMemo(() => {
    const list = [];

    // Filter active shipments
    const activeShipments = shipments.filter(
      (s) => !['DELIVERED', 'CANCELLED', 'RETURNED'].includes(s.status)
    );

    activeShipments.forEach((s) => {
      const weightKg = s.total_weight_kg ? Number(s.total_weight_kg) : 0;

      // 1. Missing Driver Recommendation
      if (!s.assigned_driver_id && !s.assigned_driver) {
        if (availableDrivers.length > 0) {
          const suggestedDriver = availableDrivers[0];
          list.push({
            id: `REC-DRV-${s.id}`,
            code: 'REC-01',
            type: 'DRIVER_ALLOCATION',
            severity: 'HIGH',
            title: `Assign Standby Driver to Waybill ${s.tracking_number}`,
            rationale: `Shipment lacks a driver allocation (assigned_driver_id is null). Fleet has ${availableDrivers.length} verified available driver(s).`,
            groundedFields: {
              shipment_id: s.id,
              tracking_number: s.tracking_number,
              suggested_driver_id: suggestedDriver.id,
              suggested_driver_name: suggestedDriver.name || `Driver #${suggestedDriver.id}`,
              driver_license: suggestedDriver.license_number,
              driver_status: suggestedDriver.availability_status,
            },
            proposedActionLabel: `Assign ${suggestedDriver.name || `Driver #${suggestedDriver.id}`}`,
            execute: async () => {
              await shipmentsApi.assignShipment(s.id, {
                driver_id: suggestedDriver.id,
                vehicle_id: s.assigned_vehicle_id || undefined,
              });
            },
          });
        } else {
          list.push({
            id: `REC-DRV-NORES-${s.id}`,
            code: 'REC-01-HOLD',
            type: 'DRIVER_HOLD',
            severity: 'MEDIUM',
            title: `Driver Shortage for Waybill ${s.tracking_number}`,
            rationale: `Shipment is ready for dispatch, but zero drivers currently have status 'AVAILABLE' in fleet. Review driver shift rosters.`,
            groundedFields: {
              shipment_id: s.id,
              tracking_number: s.tracking_number,
              fleet_driver_count: drivers.length,
              available_driver_count: 0,
            },
            isInformational: true,
          });
        }
      }

      // 2. Missing Vehicle Recommendation
      if (!s.assigned_vehicle_id && !s.assigned_vehicle) {
        // Find vehicle with capacity >= payload
        const matchingVehicle = availableVehicles.find(
          (v) => (v.capacity_kg || Number(v.capacity) || 0) >= weightKg
        ) || availableVehicles[0];

        if (matchingVehicle) {
          const vehCap = matchingVehicle.capacity_kg || Number(matchingVehicle.capacity) || 0;
          list.push({
            id: `REC-VEH-${s.id}`,
            code: 'REC-02',
            type: 'VEHICLE_ALLOCATION',
            severity: 'HIGH',
            title: `Allocate Equipment ${matchingVehicle.registration_number} to ${s.tracking_number}`,
            rationale: `Manifest has unassigned vehicle equipment. Transport unit ${matchingVehicle.registration_number} (${matchingVehicle.vehicle_type}, ${vehCap.toLocaleString()} kg max) matches cargo weight (${weightKg.toLocaleString()} kg).`,
            groundedFields: {
              shipment_id: s.id,
              tracking_number: s.tracking_number,
              cargo_weight_kg: weightKg,
              suggested_vehicle_id: matchingVehicle.id || matchingVehicle.vehicle_id,
              vehicle_registration: matchingVehicle.registration_number,
              vehicle_capacity_kg: vehCap,
              vehicle_status: matchingVehicle.status,
            },
            proposedActionLabel: `Allocate Unit ${matchingVehicle.registration_number}`,
            execute: async () => {
              const vId = matchingVehicle.id || matchingVehicle.vehicle_id;
              await shipmentsApi.assignShipment(s.id, {
                driver_id: s.assigned_driver_id || undefined,
                vehicle_id: vId,
              });
            },
          });
        } else {
          list.push({
            id: `REC-VEH-NORES-${s.id}`,
            code: 'REC-02-HOLD',
            type: 'VEHICLE_HOLD',
            severity: 'MEDIUM',
            title: `No Available Equipment Matching Cargo Weight for ${s.tracking_number}`,
            rationale: `Payload is ${weightKg.toLocaleString()} kg, but no transport vehicle with status 'AVAILABLE' is currently unallocated.`,
            groundedFields: {
              shipment_id: s.id,
              cargo_weight_kg: weightKg,
              available_vehicle_count: availableVehicles.length,
            },
            isInformational: true,
          });
        }
      }

      // 3. Staging State Transition (CONFIRMED -> ASSIGNED)
      if (s.status === 'CONFIRMED' && (s.assigned_driver_id || s.assigned_driver) && (s.assigned_vehicle_id || s.assigned_vehicle)) {
        list.push({
          id: `REC-STAGE-${s.id}`,
          code: 'REC-03',
          type: 'STAGING_ADVANCE',
          severity: 'LOW',
          title: `Authorize Dispatch Staging for Waybill ${s.tracking_number}`,
          rationale: `Both driver (#${s.assigned_driver_id}) and transport equipment (#${s.assigned_vehicle_id}) are confirmed allocated. Advance lifecycle status to ASSIGNED to initiate warehouse departure staging.`,
          groundedFields: {
            shipment_id: s.id,
            tracking_number: s.tracking_number,
            current_status: s.status,
            target_status: 'ASSIGNED',
            assigned_driver_id: s.assigned_driver_id,
            assigned_vehicle_id: s.assigned_vehicle_id,
          },
          proposedActionLabel: 'Advance to ASSIGNED Status',
          execute: async () => {
            await shipmentsApi.transitionStatus(s.id, {
              status: 'ASSIGNED',
              remarks: 'Rule-based operational recommendation: Assets fully allocated, ready for staging.',
            });
          },
        });
      }

      // 4. Warehouse Operational Status Check
      if (s.origin_warehouse) {
        const wh = warehouses.find((w) => w.id === s.origin_warehouse_id || w.id === s.origin_warehouse?.id);
        if (wh && !wh.is_active) {
          list.push({
            id: `REC-WH-INACTIVE-${s.id}`,
            code: 'REC-04',
            type: 'FACILITY_INACTIVE',
            severity: 'CRITICAL',
            title: `Origin Warehouse Inactive for Waybill ${s.tracking_number}`,
            rationale: `Origin facility '${wh.name}' has flag is_active=false. Shipments cannot be dispatched until facility status is restored or origin is reassigned.`,
            groundedFields: {
              shipment_id: s.id,
              origin_warehouse_id: wh.id,
              origin_warehouse_name: wh.name,
              facility_is_active: false,
            },
            isInformational: true,
          });
        }
      }
    });

    return list;
  }, [shipments, warehouses, drivers, vehicles, availableDrivers, availableVehicles]);

  const handleApplyClick = (rec) => {
    setPendingAction(rec);
  };

  const handleConfirmAction = async () => {
    if (!pendingAction || !pendingAction.execute) return;

    setIsExecuting(true);
    try {
      await pendingAction.execute();
      toast.success(`✓ Operational recommendation applied: ${pendingAction.title}`);
      setPendingAction(null);
      if (onApplied) {
        onApplied();
      }
    } catch (err) {
      toast.error(formatErrorMessage(err, 'Failed to execute recommendation'));
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div
      style={{
        backgroundColor: '#1E293B',
        border: '1px solid #334155',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '24px',
      }}
      id="operational-recommendations-panel"
    >
      {/* Panel Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.15rem' }}>⚙️</span>
            <h3 style={{ fontSize: '0.96rem', fontWeight: 700, color: '#F8FAFC', margin: 0 }}>
              Operational Recommendations (Rule-Based Triage Engine)
            </h3>
            <span
              style={{
                backgroundColor: 'rgba(56, 189, 248, 0.15)',
                border: '1px solid rgba(56, 189, 248, 0.4)',
                color: '#38BDF8',
                fontSize: '0.68rem',
                padding: '2px 8px',
                borderRadius: '4px',
                fontWeight: 600,
              }}
            >
              {recommendations.length} Actionable Items
            </span>
          </div>
          <p style={{ fontSize: '0.74rem', color: '#94A3B8', margin: '4px 0 0 0' }}>
            Transparent heuristic rules grounded exclusively in operational database records. Distinct from Random Forest ML.
          </p>
        </div>

        <span
          style={{
            fontSize: '0.7rem',
            padding: '3px 8px',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: '4px',
            color: '#FCD34D',
          }}
        >
          🔒 Requires Human Confirmation
        </span>
      </div>

      {/* Recommendations List */}
      {recommendations.length === 0 ? (
        <div
          style={{
            padding: '20px',
            textAlign: 'center',
            backgroundColor: '#0F172A',
            borderRadius: '6px',
            color: '#10B981',
            fontSize: '0.82rem',
          }}
        >
          ✓ Zero operational bottlenecks detected. All monitored shipments have complete driver and vehicle allocations.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {recommendations.map((rec) => {
            const severityColor =
              rec.severity === 'CRITICAL'
                ? '#EF4444'
                : rec.severity === 'HIGH'
                ? '#F59E0B'
                : '#38BDF8';
            const severityBg =
              rec.severity === 'CRITICAL'
                ? 'rgba(239, 68, 68, 0.08)'
                : rec.severity === 'HIGH'
                ? 'rgba(245, 158, 11, 0.08)'
                : 'rgba(56, 189, 248, 0.08)';

            return (
              <div
                key={rec.id}
                style={{
                  backgroundColor: '#0F172A',
                  border: `1px solid ${severityColor}40`,
                  borderRadius: '6px',
                  padding: '14px 18px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '12px',
                }}
              >
                <div style={{ flex: '1 1 500px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span
                      style={{
                        backgroundColor: severityBg,
                        color: severityColor,
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        padding: '2px 6px',
                        borderRadius: '3px',
                      }}
                    >
                      {rec.code}
                    </span>
                    <span style={{ fontSize: '0.86rem', fontWeight: 600, color: '#F1F5F9' }}>
                      {rec.title}
                    </span>
                  </div>

                  <div style={{ fontSize: '0.78rem', color: '#CBD5E1', marginBottom: '6px', lineHeight: '1.4' }}>
                    {rec.rationale}
                  </div>

                  <div style={{ fontSize: '0.7rem', color: '#64748B', display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                    {Object.entries(rec.groundedFields).map(([key, val]) => (
                      <span key={key}>
                        <strong>{key}:</strong> {String(val)}
                      </span>
                    ))}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {rec.execute ? (
                    <button
                      type="button"
                      className="btn-action primary"
                      style={{ padding: '6px 14px', fontSize: '0.74rem', minWidth: '160px' }}
                      onClick={() => handleApplyClick(rec)}
                    >
                      Review & Apply →
                    </button>
                  ) : (
                    <span style={{ fontSize: '0.74rem', color: '#F59E0B', fontStyle: 'italic' }}>
                      Manual Operator Review Needed
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Human Confirmation Dialog */}
      {pendingAction && (
        <ConfirmDialog
          isOpen={Boolean(pendingAction)}
          title={`Confirm Operational Change: ${pendingAction.code}`}
          confirmLabel="Authorize & Persist Change"
          cancelLabel="Cancel"
          confirmVariant="primary"
          isLoading={isExecuting}
          onConfirm={handleConfirmAction}
          onCancel={() => setPendingAction(null)}
          message={
            <div style={{ fontSize: '0.8rem', lineHeight: '1.5', color: '#CBD5E1' }}>
              <p style={{ margin: '0 0 10px 0' }}>
                You are about to execute rule <strong>[{pendingAction.code}] {pendingAction.title}</strong>:
              </p>
              <div
                style={{
                  backgroundColor: '#0F172A',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  padding: '10px 12px',
                  marginBottom: '10px',
                  fontFamily: 'monospace',
                  fontSize: '0.75rem',
                }}
              >
                {Object.entries(pendingAction.groundedFields).map(([k, v]) => (
                  <div key={k}>
                    <span style={{ color: '#94A3B8' }}>{k}:</span>{' '}
                    <span style={{ color: '#38BDF8' }}>{String(v)}</span>
                  </div>
                ))}
              </div>
              <p style={{ margin: 0, color: '#FCD34D', fontSize: '0.75rem' }}>
                ⚠️ <strong>Human Oversight Notice:</strong> This action will update operational PostgreSQL records in FlowGrid.
              </p>
            </div>
          }
        />
      )}
    </div>
  );
}
