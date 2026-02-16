import { useState } from 'react';
import { useStatus } from '../contexts/StatusContext';
import './MessageBanner.css';

export function MessageBanner() {
  const { messages, clearStatus, clearAll } = useStatus();
  const [showFullHistory, setShowFullHistory] = useState(false);

  // Show last 2 messages
  const recentMessages = messages.slice(-2);
  const hasMore = messages.length > 2;

  if (messages.length === 0) {
    return null;
  }

  const getStatusIcon = (type: string) => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✗';
      case 'loading':
        return '⟳';
      default:
        return 'ℹ';
    }
  };

  return (
    <>
      <div className="message-banner" onClick={() => hasMore && setShowFullHistory(true)}>
        {recentMessages.map((msg) => (
          <div key={msg.id} className={`message-item ${msg.type}`}>
            <span className="message-icon">{getStatusIcon(msg.type)}</span>
            <span className="message-text">{msg.message}</span>
            <button
              className="message-close"
              onClick={(e) => {
                e.stopPropagation();
                clearStatus(msg.id);
              }}
            >
              ×
            </button>
          </div>
        ))}
        {hasMore && (
          <div className="message-more-indicator">
            Click to see {messages.length - 2} more messages
          </div>
        )}
      </div>

      {showFullHistory && (
        <div className="message-history-modal" onClick={() => setShowFullHistory(false)}>
          <div className="message-history-content" onClick={(e) => e.stopPropagation()}>
            <div className="message-history-header">
              <h3>Message History</h3>
              <div className="message-history-actions">
                <button onClick={clearAll}>Clear All</button>
                <button onClick={() => setShowFullHistory(false)}>Close</button>
              </div>
            </div>
            <div className="message-history-list">
              {messages.map((msg) => (
                <div key={msg.id} className={`message-item ${msg.type}`}>
                  <span className="message-icon">{getStatusIcon(msg.type)}</span>
                  <span className="message-text">{msg.message}</span>
                  <span className="message-timestamp">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                  <button
                    className="message-close"
                    onClick={() => clearStatus(msg.id)}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
