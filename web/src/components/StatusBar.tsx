import React from 'react';
import { useStatus } from '../contexts/StatusContext';
import './StatusBar.css';

export function StatusBar() {
  const { messages, clearStatus } = useStatus();

  if (messages.length === 0) return null;

  // Show only the most recent message
  const currentMessage = messages[messages.length - 1];

  const getIcon = (type: string) => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'loading':
        return '⟳';
      default:
        return 'ℹ';
    }
  };

  return (
    <div className={`status-bar status-bar-${currentMessage.type}`}>
      <div className="status-bar-content">
        <span className="status-bar-icon">{getIcon(currentMessage.type)}</span>
        <span className="status-bar-message">{currentMessage.message}</span>
        {currentMessage.type !== 'loading' && (
          <button
            className="status-bar-close"
            onClick={() => clearStatus(currentMessage.id)}
            aria-label="Close"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}
