import React, { useEffect } from 'react';

/**
 * Reusable Confirmation Dialog for destructive or sensitive operations.
 *
 * @param {Object} props
 * @param {boolean} props.isOpen
 * @param {string} props.title
 * @param {string|React.ReactNode} props.message
 * @param {string} [props.confirmLabel='Confirm']
 * @param {string} [props.cancelLabel='Cancel']
 * @param {'danger'|'primary'|'warning'} [props.confirmVariant='danger']
 * @param {Function} props.onConfirm
 * @param {Function} props.onCancel
 * @param {boolean} [props.isLoading=false]
 */
export default function ConfirmDialog({
  isOpen,
  title = 'Confirm Action',
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  confirmVariant = 'danger',
  onConfirm,
  onCancel,
  isLoading = false,
}) {
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && !isLoading) {
        onCancel();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isLoading, onCancel]);

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop fg-confirm-backdrop" onClick={isLoading ? undefined : onCancel} role="dialog" aria-modal="true">
      <div className="modal-card fg-confirm-card" onClick={(e) => e.stopPropagation()}>
        <div className="fg-confirm-header">
          <div className={`fg-confirm-icon-wrap fg-confirm-${confirmVariant}`}>
            {confirmVariant === 'danger' && (
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            )}
            {confirmVariant === 'warning' && (
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            )}
            {confirmVariant === 'primary' && (
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 14 14" />
              </svg>
            )}
          </div>
          <div className="fg-confirm-title-block">
            <h3 className="fg-confirm-title">{title}</h3>
            <div className="fg-confirm-message">{message}</div>
          </div>
        </div>

        <div className="modal-actions fg-confirm-actions">
          <button
            type="button"
            className="btn-action outline"
            onClick={onCancel}
            disabled={isLoading}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className={`btn-action ${confirmVariant === 'danger' ? 'danger' : 'primary'}`}
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? 'Processing...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
