import type { Zone, Source, SystemStatus } from '../types/nuvo';
import { config } from './config';

// Request queue and deduplication
const pendingRequests = new Map<string, Promise<any>>();
const requestQueue: Array<() => Promise<any>> = [];
let isProcessingQueue = false;

class ApiClient {
  setBaseUrl(url: string) {
    config.setBaseUrl(url);
  }

  private async retryWithBackoff<T>(
    fn: () => Promise<T>,
    maxRetries = 3,
    initialDelay = 500
  ): Promise<T> {
    let lastError: Error;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error as Error;

        // Don't retry on client errors (4xx), only server errors (5xx) and network errors
        if (error instanceof Error && error.message.includes('4')) {
          throw error;
        }

        if (attempt < maxRetries - 1) {
          const delay = initialDelay * Math.pow(2, attempt); // Exponential backoff
          console.log(`Request failed (attempt ${attempt + 1}/${maxRetries}), retrying in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    throw lastError!;
  }

  private async deduplicatedRequest<T>(key: string, fn: () => Promise<T>): Promise<T> {
    // If same request is already in flight, return the existing promise
    if (pendingRequests.has(key)) {
      console.log(`Deduplicating request: ${key}`);
      return pendingRequests.get(key)!;
    }

    // Create new request with retry logic
    const promise = this.retryWithBackoff(fn)
      .finally(() => {
        // Remove from pending when complete
        pendingRequests.delete(key);
      });

    pendingRequests.set(key, promise);
    return promise;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const requestKey = `${options?.method || 'GET'}:${endpoint}`;

    return this.deduplicatedRequest(requestKey, async () => {
      const url = `${config.getApiUrl()}${endpoint}`;
      console.log('Fetching:', url);

      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      console.log(`Response from ${endpoint}:`, data);

      if (endpoint === '/zones' && data.length > 0) {
        console.log('First zone from API:', data[0]);
        console.log('First zone volume from API:', data[0].volume);
        console.log('First zone party_mode from API:', data[0].party_mode);
      }

      return data;
    });
  }

  async getStatus(): Promise<SystemStatus> {
    return this.request<SystemStatus>('/control/status');
  }

  async getHealth(): Promise<{ status: string; device: string }> {
    return this.request<{ status: string; device: string }>('/control/health');
  }

  async getZones(): Promise<Zone[]> {
    return this.request<Zone[]>('/zones');
  }

  async getZone(zoneNumber: number): Promise<Zone> {
    return this.request<Zone>(`/zones/${zoneNumber}`);
  }

  async powerOn(zoneNumber: number): Promise<void> {
    // Don't deduplicate control commands (user might press button multiple times)
    return this.retryWithBackoff(async () => {
      await fetch(`${config.getApiUrl()}/zones/${zoneNumber}/power/on`, { method: 'POST' });
    }, 2, 200); // Fewer retries for control commands
  }

  async powerOff(zoneNumber: number): Promise<void> {
    return this.retryWithBackoff(async () => {
      await fetch(`${config.getApiUrl()}/zones/${zoneNumber}/power/off`, { method: 'POST' });
    }, 2, 200);
  }

  async setVolume(zoneNumber: number, volume: number): Promise<void> {
    return this.retryWithBackoff(async () => {
      await fetch(`${config.getApiUrl()}/zones/${zoneNumber}/volume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ volume }),
      });
    }, 2, 200);
  }

  async toggleMute(zoneNumber: number): Promise<void> {
    return this.retryWithBackoff(async () => {
      await fetch(`${config.getApiUrl()}/zones/${zoneNumber}/mute`, { method: 'POST' });
    }, 2, 200);
  }

  async setSource(zoneNumber: number, sourceGuid: string): Promise<void> {
    return this.retryWithBackoff(async () => {
      await fetch(`${config.getApiUrl()}/zones/${zoneNumber}/source`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_guid: sourceGuid }),
      });
    }, 2, 200);
  }

  async getSources(): Promise<Source[]> {
    return this.request<Source[]>('/sources');
  }

  async togglePartyMode(): Promise<void> {
    return this.retryWithBackoff(async () => {
      await fetch(`${config.getApiUrl()}/control/partymode`, { method: 'POST' });
    }, 2, 200);
  }

  async allOff(): Promise<void> {
    return this.retryWithBackoff(async () => {
      await fetch(`${config.getApiUrl()}/control/alloff`, { method: 'POST' });
    }, 2, 200);
  }
}

export const api = new ApiClient();
