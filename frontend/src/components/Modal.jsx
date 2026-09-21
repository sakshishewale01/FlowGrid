import React, { useEffect } from 'react';

/**
 * Base accessible Modal component.
 *
 * @param {Object} props
 * @param {boolean} props.isOpen
 * @param {Function} props.onClose
 * @param {string} props.title
 * @param {string} [props.subtitle]
 * @param {React.ReactNode} [props.icon]
 * @param {'small'|'medium'|'large'|'drawer'} [props.size='medium']
 * @param {React.ReactNode} props.children
 * @param {React.ReactNode} [props.footer]
 */
export default function Modal({
  isOpen,
  onClose,
  title,
  subtitle,
  icon,
  size = 'medium',
  children,
  footer,
}) {
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClass = size === 'large' ? 'modal-card-large' : size === 'drawer' ? 'drawer-card' : size === 'small' ? 'modal-card-small' : '';

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className={`modal-card ${sizeClass}`} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          {icon && <div className="modal-header-icon">{icon}</div>}
          <div className="modal-header-text">
            <h2 className="modal-title">{title}</h2>
            {subtitle && <p className="modal-subtitle">{subtitle}</p>}
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            ×
          </button>
        </div>

        <div className="modal-body-content">
          {children}
        </div>

        {footer && (
          <div className="modal-footer">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
