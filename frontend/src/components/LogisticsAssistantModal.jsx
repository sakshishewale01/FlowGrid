import React, { useState, useEffect, useRef, useCallback } from 'react';
import { assistantApi } from '../api/assistant.js';
import { shipmentsApi } from '../api/shipments.js';
import { formatErrorMessage } from '../api/client.js';

export default function LogisticsAssistantModal({ isOpen, onClose, onNavigate }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeShipmentId, setActiveShipmentId] = useState(1);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Fetch real available shipment ID to ground the suggested chip
  useEffect(() => {
    async function loadSampleShipment() {
      try {
        const list = await shipmentsApi.listShipments({ limit: 3 });
        if (list && list.length > 0 && list[0].id) {
          setActiveShipmentId(list[0].id);
        }
      } catch {
        // Fall back gracefully to ID 1
      }
    }
    loadSampleShipment();
  }, []);

  // Initialize greeting on first open
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: 'welcome-1',
          sender: 'assistant',
          text: `👋 **Welcome to the FlowGrid Grounded Logistics Assistant.**\n\nI provide explainable logistics intelligence grounded strictly in **live operational database records**, deterministic heuristic rules, and verified control tower workflows.\n\n🛡️ **Strict Integrity Policy:** I refuse to invent fake shipments, driver locations, weather forecasts, or arbitrary numbers.\n\nSelect a question chip below or ask anything about active freight manifests:`,
          sources: [
            {
              source_type: 'SYSTEM_GUIDANCE',
              title: 'Grounded Intent-Based Assistant',
              content: 'Decoupled from third-party LLMs. Zero hallucination guarantee.',
            },
          ],
          suggestedChips: [
            'How do I use the Shipment Rescue Center?',
            `What is the status of shipment ${activeShipmentId}?`,
            'Which shipments need attention according to the available data?',
            'What does the delay prediction mean?',
            'How does the What-If Disruption Simulator work?',
          ],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    }
  }, [messages.length, activeShipmentId]);

  // Scroll to bottom when messages update
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen, messages, scrollToBottom]);

  if (!isOpen) return null;

  const handleSendMessage = async (queryText) => {
    const text = (queryText || inputValue).trim();
    if (!text || isLoading) return;

    setError(null);
    setInputValue('');

    const userMsg = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await assistantApi.query(text);
      const assistantMsg = {
        id: `asst-${Date.now()}`,
        sender: 'assistant',
        text: response.answer,
        intent: response.intent,
        sources: response.sources || [],
        suggestedChips: response.suggested_chips || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(formatErrorMessage(err, 'Failed to consult assistant service'));
      const errorMsg = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        isError: true,
        text: `⚠️ **Communication Notice:** Unable to reach the assistant service. Please verify your connection or retry your query.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    setMessages([]);
    setError(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Helper to format basic markdown-like text
  const renderFormattedText = (text) => {
    if (!text) return null;
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      // Headers
      if (line.startsWith('### ')) {
        return (
          <h4 key={idx} style={{ fontSize: '0.92rem', fontWeight: 700, color: '#38BDF8', margin: '8px 0 4px 0' }}>
            {line.replace('### ', '')}
          </h4>
        );
      }
      // Bullet items
      if (line.startsWith('• ') || line.startsWith('- ')) {
        return (
          <div key={idx} style={{ paddingLeft: '12px', margin: '3px 0', display: 'flex', gap: '6px' }}>
            <span style={{ color: '#38BDF8' }}>•</span>
            <span>{renderInlineFormatting(line.replace(/^[•-]\s*/, ''))}</span>
          </div>
        );
      }
      // Numbered lists
      const numMatch = line.match(/^(\d+\.)\s+(.*)/);
      if (numMatch) {
        return (
          <div key={idx} style={{ paddingLeft: '12px', margin: '4px 0', display: 'flex', gap: '6px' }}>
            <span style={{ color: '#FCD34D', fontWeight: 600 }}>{numMatch[1]}</span>
            <span>{renderInlineFormatting(numMatch[2])}</span>
          </div>
        );
      }
      // Blank lines
      if (!line.trim()) {
        return <div key={idx} style={{ height: '6px' }} />;
      }
      return (
        <p key={idx} style={{ margin: '3px 0' }}>
          {renderInlineFormatting(line)}
        </p>
      );
    });
  };

  const renderInlineFormatting = (str) => {
    // Bold **text**
    const parts = str.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} style={{ color: '#F8FAFC' }}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code
            key={i}
            style={{
              backgroundColor: 'rgba(15, 23, 42, 0.7)',
              border: '1px solid #334155',
              padding: '1px 5px',
              borderRadius: '3px',
              color: '#38BDF8',
              fontFamily: 'monospace',
              fontSize: '0.75rem',
            }}
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  return (
    <div
      className="modal-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="assistant-modal-title"
      style={{ zIndex: 1100 }}
    >
      <div
        className="modal-card"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '92vw',
          maxWidth: '780px',
          height: '85vh',
          maxHeight: '850px',
          display: 'flex',
          flexDirection: 'column',
          padding: 0,
          backgroundColor: '#0F172A',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.7)',
        }}
      >
        {/* Assistant Header */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid #1E293B',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: '#1E293B',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #0284C7 0%, #2563EB 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 8px rgba(2, 132, 199, 0.4)',
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 id="assistant-modal-title" style={{ fontSize: '1rem', fontWeight: 700, color: '#F8FAFC', margin: 0 }}>
                  FlowGrid Logistics Assistant
                </h2>
                <span
                  style={{
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    color: '#10B981',
                    border: '1px solid rgba(16, 185, 129, 0.4)',
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    padding: '1px 6px',
                    borderRadius: '4px',
                  }}
                >
                  GROUNDED INTENT AI
                </span>
              </div>
              <p style={{ fontSize: '0.72rem', color: '#94A3B8', margin: '2px 0 0 0' }}>
                Answers grounded in live PostgreSQL records and heuristic triage rules. Zero hallucinated data.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              type="button"
              className="btn-action outline"
              style={{ padding: '3px 8px', fontSize: '0.7rem' }}
              onClick={handleClearHistory}
              title="Reset current chat session"
            >
              Clear Chat
            </button>
            <button
              type="button"
              className="modal-close-btn"
              onClick={onClose}
              aria-label="Close assistant"
              style={{ position: 'static' }}
            >
              ×
            </button>
          </div>
        </div>

        {/* Chat History Viewport */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            backgroundColor: '#0B132B',
          }}
        >
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: isUser ? 'flex-end' : 'flex-start',
                  maxWidth: '100%',
                }}
              >
                <div
                  style={{
                    maxWidth: isUser ? '80%' : '90%',
                    backgroundColor: isUser ? '#1E3A8A' : '#1E293B',
                    border: isUser ? '1px solid #2563EB' : '1px solid #334155',
                    borderRadius: isUser ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                    padding: '12px 16px',
                    color: '#F1F5F9',
                    fontSize: '0.82rem',
                    lineHeight: '1.5',
                  }}
                >
                  {isUser ? (
                    <div>{msg.text}</div>
                  ) : (
                    <div>
                      {renderFormattedText(msg.text)}

                      {/* Transparency Sources Citation Block */}
                      {msg.sources && msg.sources.length > 0 && (
                        <div
                          style={{
                            marginTop: '12px',
                            paddingTop: '10px',
                            borderTop: '1px solid #334155',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '6px',
                          }}
                        >
                          <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#94A3B8', letterSpacing: '0.05em' }}>
                            TRANSPARENCY CITATIONS &amp; GROUNDING:
                          </span>
                          {msg.sources.map((src, sIdx) => {
                            const badgeColor =
                              src.source_type === 'RETRIEVED_FACT'
                                ? '#38BDF8'
                                : src.source_type === 'OPERATIONAL_RULE'
                                ? '#F59E0B'
                                : src.source_type === 'ML_DISCLAIMER'
                                ? '#C084FC'
                                : src.source_type === 'SIMULATOR_SANDBOX'
                                ? '#22D3EE'
                                : '#94A3B8';
                            return (
                              <div
                                key={sIdx}
                                style={{
                                  backgroundColor: 'rgba(15, 23, 42, 0.8)',
                                  border: `1px solid ${badgeColor}35`,
                                  borderRadius: '4px',
                                  padding: '6px 8px',
                                  fontSize: '0.7rem',
                                }}
                              >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                                  <span style={{ color: badgeColor, fontWeight: 700 }}>
                                    [{src.source_type.replace(/_/g, ' ')}]
                                  </span>
                                  <strong style={{ color: '#E2E8F0' }}>{src.title}</strong>
                                </div>
                                <div style={{ color: '#94A3B8', fontSize: '0.68rem' }}>{src.content}</div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}

                  <div
                    style={{
                      marginTop: '4px',
                      fontSize: '0.65rem',
                      color: isUser ? '#93C5FD' : '#64748B',
                      textAlign: isUser ? 'right' : 'left',
                    }}
                  >
                    {msg.timestamp}
                  </div>
                </div>

                {/* Follow-up Suggested Question Chips */}
                {!isUser && msg.suggestedChips && msg.suggestedChips.length > 0 && (
                  <div
                    style={{
                      marginTop: '8px',
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '6px',
                      maxWidth: '90%',
                    }}
                  >
                    {msg.suggestedChips.map((chip, cIdx) => (
                      <button
                        key={cIdx}
                        type="button"
                        onClick={() => handleSendMessage(chip)}
                        disabled={isLoading}
                        style={{
                          backgroundColor: '#1E293B',
                          border: '1px solid rgba(56, 189, 248, 0.4)',
                          color: '#38BDF8',
                          fontSize: '0.72rem',
                          padding: '4px 10px',
                          borderRadius: '14px',
                          cursor: 'pointer',
                          textAlign: 'left',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        💬 {chip}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          {/* Loading Indicator */}
          {isLoading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#38BDF8', fontSize: '0.78rem' }}>
              <span className="spinner-inline" style={{ width: '12px', height: '12px' }} />
              <span>Consulting operational database and heuristic triage rules...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input & Quick Chips Bar */}
        <div
          style={{
            padding: '14px 20px',
            backgroundColor: '#1E293B',
            borderTop: '1px solid #334155',
          }}
        >
          {error && (
            <div
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid #EF4444',
                color: '#EF4444',
                fontSize: '0.72rem',
                padding: '4px 8px',
                borderRadius: '4px',
                marginBottom: '8px',
              }}
            >
              {error}
            </div>
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            style={{ display: 'flex', gap: '8px', alignItems: 'center' }}
          >
            <input
              ref={inputRef}
              type="text"
              className="form-input"
              style={{ flex: 1, padding: '8px 12px', fontSize: '0.82rem' }}
              placeholder="Ask about shipment status, triage rules, ML delay predictions..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              aria-label="Assistant query input"
            />
            <button
              type="submit"
              className="btn-action primary"
              disabled={isLoading || !inputValue.trim()}
              style={{ padding: '8px 16px', fontSize: '0.8rem', minWidth: '80px' }}
            >
              {isLoading ? '...' : 'Send'}
            </button>
          </form>

          <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.68rem', color: '#64748B' }}>
            <span>FlowGrid Grounded AI • Read-Only Session • Press Enter to Send</span>
            <span>Zero Hallucination Guaranteed</span>
          </div>
        </div>
      </div>
    </div>
  );
}
