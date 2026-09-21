import React, { createContext, useContext, useState, useCallback } from 'react';

const ToastContext = createContext(null);

let toastIdCounter = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((current) => current.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback((message, type = 'info', duration = 4000) => {
    const id = ++toastIdCounter;
    const newToast = { id, message, type };

    setToasts((current) => [...current, newToast]);

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }

    return id;
  }, [removeToast]);

  const toast = {
    success: (msg, duration) => showToast(msg, 'success', duration),
    error: (msg, duration) => showToast(msg, 'error', duration || 5000),
    info: (msg, duration) => showToast(msg, 'info', duration),
    warning: (msg, duration) => showToast(msg, 'warning', duration || 4500),
    dismiss: removeToast,
  };

  return (
    <ToastContext.Provider value={{ toast, showToast, removeToast }}>
      {children}
      <div className="flowgrid-toast-container" aria-live="polite" aria-atomic="true">
        {toasts.map((t) => (
          <div key={t.id} className={`flowgrid-toast flowgrid-toast-${t.type}`} role="alert">
            <span className="flowgrid-toast-icon">
              {t.type === 'success' && '✓'}
              {t.type === 'error' && '✕'}
              {t.type === 'warning' && '⚠'}
              {t.type === 'info' && 'ℹ'}
            </span>
            <span className="flowgrid-toast-message">{t.message}</span>
            <button
              type="button"
              className="flowgrid-toast-close"
              onClick={() => removeToast(t.id)}
              aria-label="Close notification"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    // Fallback safe dummy if used outside ToastProvider
    return {
      toast: {
        success: (m) => console.log('Toast success:', m),
        error: (m) => console.error('Toast error:', m),
        info: (m) => console.log('Toast info:', m),
        warning: (m) => console.warn('Toast warning:', m),
        dismiss: () => {},
      },
      showToast: () => {},
      removeToast: () => {},
    };
  }
  return context;
}

export default ToastContext;
