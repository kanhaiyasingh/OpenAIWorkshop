import { useState, useEffect, useRef, useCallback } from 'react';
import { WS_CONFIG } from '../constants/config';

/**
 * Custom hook for managing WebSocket connections with automatic reconnection
 * Uses a message queue to ensure no messages are lost when they arrive quickly
 * @param {string} url - WebSocket URL to connect to
 * @returns {Object} Object containing lastMessage, readyState, and sendMessage function
 */
export function useWebSocket(url) {
  const [lastMessage, setLastMessage] = useState(null);
  const [readyState, setReadyState] = useState('CONNECTING');
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);
  const reconnectAttempts = useRef(0);
  
  // Message queue to prevent lost messages during rapid updates
  const messageQueue = useRef([]);
  const processingQueue = useRef(false);

  // Process messages from queue one at a time
  const processQueue = useCallback(() => {
    if (processingQueue.current || messageQueue.current.length === 0) {
      return;
    }
    
    processingQueue.current = true;
    const message = messageQueue.current.shift();
    
    // Use setTimeout to ensure React processes each state update
    setLastMessage(message);
    
    // Schedule next message processing
    setTimeout(() => {
      processingQueue.current = false;
      processQueue();
    }, 0);
  }, []);

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setReadyState('OPEN');
        reconnectAttempts.current = 0;
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Add to queue instead of directly setting state
          messageQueue.current.push(data);
          processQueue();
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setReadyState('CLOSED');

        // Attempt to reconnect if under max attempts
        if (reconnectAttempts.current < WS_CONFIG.MAX_RECONNECT_ATTEMPTS) {
          reconnectTimeout.current = setTimeout(() => {
            reconnectAttempts.current += 1;
            console.log(
              `Attempting to reconnect... (${reconnectAttempts.current}/${WS_CONFIG.MAX_RECONNECT_ATTEMPTS})`
            );
            connect();
          }, WS_CONFIG.RECONNECT_DELAY);
        } else {
          console.error('Max reconnection attempts reached');
        }
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
    }
  }, [url, processQueue]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not open. Ready state:', ws.current?.readyState);
    }
  }, []);

  return {
    lastMessage,
    readyState,
    sendMessage,
  };
}
