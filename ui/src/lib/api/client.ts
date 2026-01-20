/** API client wrapper for backend communication. */

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export interface HealthResponse {
  status: string;
  version: string;
  connected: boolean;
}

export interface Catalog {
  potentiometers: PotentiometerDefinition[];
  vouts: any[];
  pwms: any[];
  can_channels: any[];
  j1708: any[];
}

export interface PotentiometerDefinition {
  id: string;
  name: string;
  port: number;
  pin: string;
  resistance: string;
  ecm_fault_low: number;
  ecm_fault_high: number;
  type: string;
}

export interface DeviceState {
  sss2_version: string | null;
  last_updated: string | null;
  connected_port: string | null;
  ignition: boolean;
  potentiometers: Record<string, PotentiometerState>;
  vouts: Record<string, any>;
  pwms: Record<string, any>;
  can: Record<string, any>;
  j1708: Record<string, any>;
}

export interface PotentiometerState {
  wiper_position: number;
  term_a_connect: boolean;
  term_b_connect: boolean;
  wiper_connect: boolean;
  application: string;
  wire_color: string;
}

export interface Snapshot {
  id: string;
  label: string;
  created_at: string;
}

export interface IgnitionRequest {
  on: boolean;
}

export interface IgnitionResponse {
  accepted: boolean;
  executed: boolean;
  detail: string;
  confirmation: string | null;
  ignition: boolean;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  async getCatalog(): Promise<Catalog> {
    return this.request<Catalog>('/catalog');
  }

  async getState(): Promise<DeviceState> {
    return this.request<DeviceState>('/sss2/state');
  }

  async updateState(state: Partial<DeviceState>): Promise<DeviceState> {
    return this.request<DeviceState>('/sss2/state', {
      method: 'PUT',
      body: JSON.stringify({ state }),
    });
  }

  async setIgnition(on: boolean): Promise<IgnitionResponse> {
    return this.request<IgnitionResponse>('/sss2/ignition', {
      method: 'POST',
      body: JSON.stringify({ on }),
    });
  }

  async createSnapshot(label?: string): Promise<Snapshot> {
    return this.request<Snapshot>('/snapshots', {
      method: 'POST',
      body: JSON.stringify({ label: label || null }),
    });
  }

  async listSnapshots(): Promise<Snapshot[]> {
    return this.request<Snapshot[]>('/snapshots');
  }

  async revertSnapshot(snapshotId: string): Promise<DeviceState> {
    return this.request<DeviceState>(`/snapshots/${snapshotId}/revert`, {
      method: 'POST',
    });
  }

  async deleteSnapshot(snapshotId: string): Promise<void> {
    await this.request(`/snapshots/${snapshotId}`, {
      method: 'DELETE',
    });
  }
}

export const apiClient = new ApiClient();
