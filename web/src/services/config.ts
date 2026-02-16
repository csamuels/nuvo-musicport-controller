/**
 * Global configuration for API and WebSocket URLs
 */

class Config {
  private _baseUrl: string = '';

  setBaseUrl(url: string) {
    // Remove trailing slash
    this._baseUrl = url.replace(/\/$/, '');
  }

  getApiUrl(): string {
    const url = this._baseUrl ? `${this._baseUrl}/api` : '/api';
    console.log('config.getApiUrl() returning:', url, '(baseUrl:', this._baseUrl, ')');
    return url;
  }

  getWebSocketUrl(): string {
    if (!this._baseUrl) {
      return 'ws://localhost:8000/ws';
    }

    // Convert http://host:port to ws://host:port/ws
    const wsUrl = this._baseUrl.replace(/^http/, 'ws');
    return `${wsUrl}/ws`;
  }
}

export const config = new Config();
