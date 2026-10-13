import React, { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('FlowGrid Component Error Caught:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="auth-alert error" style={{ margin: '24px', padding: '20px' }} role="alert">
          <div className="auth-alert-content">
            <span className="auth-alert-title" style={{ fontSize: '1rem', fontWeight: 600 }}>
              Operational View Error
            </span>
            <span className="auth-alert-text" style={{ marginTop: '6px', fontSize: '0.85rem' }}>
              {this.state.error?.message || 'An unexpected rendering error occurred while loading this view.'}
            </span>
          </div>
          <button
            type="button"
            className="btn-action outline"
            onClick={this.handleReset}
            style={{ marginTop: '12px', alignSelf: 'flex-start' }}
          >
            Reload View
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
