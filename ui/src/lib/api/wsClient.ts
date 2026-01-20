/** WebSocket client for connection status updates. */

export interface ConnectionStatusMessage {
  type: 'connection_status';
  connected: boolean;
  port: string;
  message: string | null;
}

export type ConnectionStatusCallback = (status: ConnectionStatusMessage) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectInterval: number = 3000; // 3 seconds
  private reconnectTimer: number | null = null;
  private callbacks: Set<ConnectionStatusCallback> = new Set();
  private url: string;

  constructor(url: string = '/api/connection/ws') {
    this.url = url.startsWith('ws') ? url : 
      `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}${url}`;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      this.ws = new WebSocket(this.url);
      this.setupEventHandlers();
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.scheduleReconnect();
    }
  }

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    };

    this.ws.onmessage = (event) => {
      try {
        const message: ConnectionStatusMessage = JSON.parse(event.data);
        if (message.type === 'connection_status') {
          this.notifyCallbacks(message);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.ws = null;
      this.scheduleReconnect();
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;

    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      console.log('Attempting to reconnect WebSocket...');
      this.connect();
    }, this.reconnectInterval);
  }

  private notifyCallbacks(message: ConnectionStatusMessage): void {
    this.callbacks.forEach(callback => {
      try {
        callback(message);
      } catch (error) {
        console.error('Error in connection status callback:', error);
      }
    });
  }

  subscribe(callback: ConnectionStatusCallback): () => void {
    this.callbacks.add(callback);
    
    // Return unsubscribe function
    return () => {
      this.callbacks.delete(callback);
    };
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.callbacks.clear();
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
let wsClientInstance: WebSocketClient | null = null;

export function connectWebSocket(): WebSocketClient {
  if (!wsClientInstance) {
    wsClientInstance = new WebSocketClient();
    wsClientInstance.connect();
  }
  return wsClientInstance;
}

export function disconnectWebSocket(): void {
  if (wsClientInstance) {
    wsClientInstance.disconnect();
    wsClientInstance = null;
  }
}

export function getWebSocketClient(): WebSocketClient | null {
  return wsClientInstance;
}
