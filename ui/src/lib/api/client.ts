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
  potentiometer_power_groups?: Record<string, PotentiometerPowerGroup>;
  vouts: Record<string, any>;
  pwms: Record<string, any>;
  can: Record<string, any>;
  j1708: Record<string, any>;
}

export interface PotentiometerState {
  wiper_position: number;
  voltage: number;  // Calculated based on power setting (0-5V or 0-12V)
  enabled: boolean;  // On/Off state (default: false)
  // Removed: term_a_connect, term_b_connect, wiper_connect
  application?: string;  // Deprecated - now from ECU
  wire_color?: string;  // Deprecated - now from ECU
}

export interface PotentiometerPowerGroup {
  group_id: string;  // e.g., "1-2", "3-4"
  voltage_setting: '5V' | '12V';  // Selected voltage
  potentiometers: string[];  // Pot IDs in this group, e.g., ["po1", "po2"]
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

export interface PinConfiguration {
  wire_color: string;
  ecu_function: string;
}

export interface ECUItem {
  id: string;
  name: string;
  model: string;
  serial_number: string;
  created_at: string;
  updated_at: string;
}

export interface ECUFull {
  id: string;
  name: string;
  model: string;
  serial_number: string;
  pictures: string[];
  pins: Record<string, PinConfiguration>;
  created_at: string;
  updated_at: string;
}

export interface ECUCreate {
  name: string;
  model?: string;
  serial_number?: string;
  pictures?: string[];
  pins?: Record<string, PinConfiguration>;
}

export interface ECUUpdate {
  name?: string;
  model?: string;
  serial_number?: string;
  pictures?: string[];
  pins?: Record<string, PinConfiguration>;
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

  async listECUs(): Promise<ECUItem[]> {
    return this.request<ECUItem[]>('/ecu');
  }

  async getECU(ecuId: string): Promise<ECUFull> {
    return this.request<ECUFull>(`/ecu/${ecuId}`);
  }

  async createECU(ecu: ECUCreate): Promise<ECUFull> {
    return this.request<ECUFull>('/ecu', {
      method: 'POST',
      body: JSON.stringify(ecu),
    });
  }

  async updateECU(ecuId: string, updates: ECUUpdate): Promise<ECUFull> {
    return this.request<ECUFull>(`/ecu/${ecuId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteECU(ecuId: string): Promise<void> {
    await this.request(`/ecu/${ecuId}`, {
      method: 'DELETE',
    });
  }
}

export const apiClient = new ApiClient();
