import type { Zone, Source, SystemStatus } from '../types/nuvo';

const API_BASE = '/api';

class ApiClient {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  async getStatus(): Promise<SystemStatus> {
    return this.request<SystemStatus>('/control/status');
  }

  async getZones(): Promise<Zone[]> {
    return this.request<Zone[]>('/zones');
  }

  async getZone(zoneNumber: number): Promise<Zone> {
    return this.request<Zone>(`/zones/${zoneNumber}`);
  }

  async powerOn(zoneNumber: number): Promise<void> {
    await this.request(`/zones/${zoneNumber}/power/on`, { method: 'POST' });
  }

  async powerOff(zoneNumber: number): Promise<void> {
    await this.request(`/zones/${zoneNumber}/power/off`, { method: 'POST' });
  }

  async setVolume(zoneNumber: number, volume: number): Promise<void> {
    await this.request(`/zones/${zoneNumber}/volume`, {
      method: 'POST',
      body: JSON.stringify({ volume }),
    });
  }

  async toggleMute(zoneNumber: number): Promise<void> {
    await this.request(`/zones/${zoneNumber}/mute`, { method: 'POST' });
  }

  async setSource(zoneNumber: number, sourceGuid: string): Promise<void> {
    await this.request(`/zones/${zoneNumber}/source`, {
      method: 'POST',
      body: JSON.stringify({ source_guid: sourceGuid }),
    });
  }

  async getSources(): Promise<Source[]> {
    return this.request<Source[]>('/sources');
  }

  async togglePartyMode(): Promise<void> {
    await this.request('/control/partymode', { method: 'POST' });
  }

  async allOff(): Promise<void> {
    await this.request('/control/alloff', { method: 'POST' });
  }
}

export const api = new ApiClient();
