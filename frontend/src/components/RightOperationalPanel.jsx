import React, { useState } from 'react';
import { assistantApi } from '../api/assistant.js';
import { formatErrorMessage } from '../api/client.js';

/**
 * RightOperationalPanel
 * Matches the reference right-column structure:
 * 1. Immediate Attention Required (actionable alerts)
 * 2. Predict Corridor Delay (ML) (quick entry to ML prediction engine)
 * 3. FlowGrid Assistant (embedded interactive grounded assistant)
 */
export default function RightOperationalPanel({ onNavigate, onOpenPredictor }) {
  // Assistant Chat states
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'bot',
      text: 'How can I help you today?',
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const suggestedQuestions = [
    'How do I use the Shipment Rescue Center?',
    'What is the status of a shipment?',
    'Which shipments need attention?',
    'What does the delay prediction mean?',
    'How does the What-If Disruption Simulator work?',
  ];

  const handleSendQuery = async (queryText) => {
    const q = (queryText || inputQuery).trim();
    if (!q || isLoading) return;

    setInputQuery('');
    setMessages((prev) => [
      ...prev,
      { id: `user-${Date.now()}`, sender: 'user', text: q },
    ]);
    setIsLoading(true);

    try {
      const response = await assistantApi.query(q);
      setMessages((prev) => [
        ...prev,
        {
          id: `bot-${Date.now()}`,
          sender: 'bot',
          text: response.answer,
          sources: response.sources || [],
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `bot-err-${Date.now()}`,
          sender: 'bot',
          text: `⚠️ Query resolution notice: ${formatErrorMessage(err)}`,
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <aside className="ref-right-panel" aria-label="Operational Attention & Intelligent Assistant">
      {/* 1. Immediate Attention Required */}
      <div className="ref-attention-card">
        <div className="attention-header">
          <div className="attention-icon-box">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F43F5E" strokeWidth="2.2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
          </div>
          <div className="attention-title-block">
            <h3 className="attention-heading">Immediate Attention Required</h3>
            <span className="attention-sub">3 shipments need your attention</span>
          </div>
          <button
            type="button"
            className="attention-view-all"
            onClick={() => onNavigate && onNavigate('rescue')}
            title="Open Shipment Rescue Center"
          >
            View all →
          </button>
        </div>

        <ul className="attention-list">
          <li
            className="attention-item"
            onClick={() => onNavigate && onNavigate('rescue')}
            role="button"
            tabIndex={0}
          >
            <span className="attention-bullet" />
            <span className="attention-text">Unassigned driver (FG-98422)</span>
          </li>
          <li
            className="attention-item"
            onClick={() => onNavigate && onNavigate('rescue')}
            role="button"
            tabIndex={0}
          >
            <span className="attention-bullet" />
            <span className="attention-text">Overloaded cargo (FG-98415)</span>
          </li>
          <li
            className="attention-item"
            onClick={() => onNavigate && onNavigate('rescue')}
            role="button"
            tabIndex={0}
          >
            <span className="attention-bullet" />
            <span className="attention-text">Missing equipment (FG-98407)</span>
          </li>
        </ul>
      </div>

      {/* 2. Predict Corridor Delay (ML) */}
      <div
        className="ref-ml-card"
        onClick={onOpenPredictor}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter') onOpenPredictor();
        }}
        title="Open ML Corridor Delay Predictor"
      >
        <div className="ml-card-left">
          <div className="ml-icon-circle">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="#38BDF8">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
          </div>
          <div className="ml-card-text">
            <div className="ml-card-title-row">
              <span className="ml-card-title">Predict Corridor Delay (ML)</span>
              <span className="ml-badge-experimental">Experimental</span>
            </div>
            <p className="ml-card-caption">Get AI-powered delay probability for any corridor.</p>
          </div>
        </div>
        <div className="ml-card-arrow">›</div>
      </div>

      {/* 3. FlowGrid Assistant Embedded Panel */}
      <div className="ref-assistant-panel" aria-label="Embedded FlowGrid Assistant">
        <div className="ref-assistant-header">
          <div className="ref-assistant-bot-avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22D3EE" strokeWidth="2">
              <rect x="3" y="11" width="18" height="10" rx="2" />
              <circle cx="12" cy="5" r="2" />
              <path d="M12 7v4" />
              <line x1="8" y1="16" x2="8.01" y2="16" />
              <line x1="16" y1="16" x2="16.01" y2="16" />
            </svg>
          </div>
          <div className="ref-assistant-header-meta">
            <h3 className="ref-assistant-title">FlowGrid Assistant</h3>
            <p className="ref-assistant-sub">Ask about shipments, operations, or get help with FlowGrid features.</p>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="ref-assistant-messages">
          {messages.map((m) => (
            <div key={m.id} className={`ref-msg-row ${m.sender}`}>
              {m.sender === 'bot' && (
                <div className="ref-msg-avatar">🤖</div>
              )}
              <div className={`ref-msg-bubble ${m.sender} ${m.isError ? 'error' : ''}`}>
                <p>{m.text}</p>
                {m.sources && m.sources.length > 0 && (
                  <div className="ref-msg-sources">
                    {m.sources.map((s, idx) => (
                      <span key={idx} className="ref-msg-source-tag">
                        {s.type.replace('_', ' ')}: {s.title}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="ref-msg-row bot">
              <div className="ref-msg-avatar">🤖</div>
              <div className="ref-msg-bubble bot loading">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          )}
        </div>

        {/* Suggested Question Chips */}
        <div className="ref-assistant-chips" aria-label="Suggested Prompts">
          {suggestedQuestions.map((chip, idx) => (
            <button
              key={idx}
              type="button"
              className="ref-chip-btn"
              onClick={() => handleSendQuery(chip)}
              disabled={isLoading}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
              <span>{chip}</span>
            </button>
          ))}
        </div>

        {/* Chat Input */}
        <form
          className="ref-assistant-form"
          onSubmit={(e) => {
            e.preventDefault();
            handleSendQuery();
          }}
        >
          <input
            type="text"
            className="ref-assistant-input"
            placeholder="Type your question..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={isLoading}
            aria-label="Assistant message prompt"
          />
          <button
            type="submit"
            className="ref-assistant-send-btn"
            disabled={!inputQuery.trim() || isLoading}
            aria-label="Submit Question"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </form>

        <div className="ref-assistant-disclaimer">
          Read-only • No changes will be made to your data.
        </div>
      </div>
    </aside>
  );
}
