import React, { createContext, useContext, useState, useCallback } from 'react';

export type StatusType = 'info' | 'success' | 'error' | 'loading';

export interface StatusMessage {
  id: string;
  type: StatusType;
  message: string;
  timestamp: number;
}

interface StatusContextType {
  messages: StatusMessage[];
  showStatus: (message: string, type: StatusType, duration?: number) => void;
  clearStatus: (id: string) => void;
  clearAll: () => void;
}

const StatusContext = createContext<StatusContextType | undefined>(undefined);

export function StatusProvider({ children }: { children: React.ReactNode }) {
  const [messages, setMessages] = useState<StatusMessage[]>([]);

  const showStatus = useCallback((message: string, type: StatusType, duration: number = 5000) => {
    const id = `${Date.now()}-${Math.random()}`;
    const newMessage: StatusMessage = {
      id,
      type,
      message,
      timestamp: Date.now(),
    };

    setMessages(prev => [...prev, newMessage]);

    // Auto-remove after duration (except for loading messages)
    if (type !== 'loading' && duration > 0) {
      setTimeout(() => {
        setMessages(prev => prev.filter(m => m.id !== id));
      }, duration);
    }

    return id;
  }, []);

  const clearStatus = useCallback((id: string) => {
    setMessages(prev => prev.filter(m => m.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setMessages([]);
  }, []);

  return (
    <StatusContext.Provider value={{ messages, showStatus, clearStatus, clearAll }}>
      {children}
    </StatusContext.Provider>
  );
}

export function useStatus() {
  const context = useContext(StatusContext);
  if (!context) {
    throw new Error('useStatus must be used within a StatusProvider');
  }
  return context;
}
