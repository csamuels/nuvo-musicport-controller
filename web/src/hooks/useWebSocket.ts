import { useEffect, useRef, useCallback } from 'react';
import type { StateChangeEvent } from '../types/nuvo';
import { config } from '../services/config';

const RECONNECT_DELAY = 3000;
const MAX_RETRIES = 5;

export function useWebSocket(onMessage: (event: StateChangeEvent) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number>();
  const isConnecting = useRef<boolean>(false);
  const retryCount = useRef<number>(0);

  const connect = useCallback(() => {
    // Prevent multiple simultaneous connection attempts
    if (isConnecting.current || (wsRef.current && wsRef.current.readyState === WebSocket.OPEN)) {
      console.log('Already connecting or connected, skipping...');
      return;
    }

    try {
      isConnecting.current = true;
      const wsUrl = config.getWebSocketUrl();
      console.log('Connecting to WebSocket:', wsUrl);
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        isConnecting.current = false;
        retryCount.current = 0; // Reset retry count on successful connection
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        isConnecting.current = false;
        // Only log errors if we've exceeded retry limit (persistent connection issues)
        if (retryCount.current >= MAX_RETRIES) {
          console.error('WebSocket error (persistent):', {
            readyState: ws.readyState,
            url: ws.url,
            retries: retryCount.current,
            error
          });
        }
      };

      ws.onclose = (event) => {
        isConnecting.current = false;

        // Only log if it's an unexpected close or we've exceeded retries
        if ((!event.wasClean || event.code !== 1000) && retryCount.current >= MAX_RETRIES) {
          console.log('WebSocket closed (persistent issue):', {
            code: event.code,
            reason: event.reason || 'No reason provided',
            wasClean: event.wasClean,
            retries: retryCount.current
          });
        }

        // Only reconnect if it wasn't a clean close
        if (!event.wasClean || event.code !== 1000) {
          retryCount.current += 1;
          reconnectTimeoutRef.current = window.setTimeout(connect, RECONNECT_DELAY);
        } else {
          // Clean close, reset retry count
          retryCount.current = 0;
        }
      };

      wsRef.current = ws;
    } catch (error) {
      isConnecting.current = false;
      console.error('Failed to connect WebSocket:', error);
      reconnectTimeoutRef.current = window.setTimeout(connect, RECONNECT_DELAY);
    }
  }, [onMessage]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return wsRef;
}
