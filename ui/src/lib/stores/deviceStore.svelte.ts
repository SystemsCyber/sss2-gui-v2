/** Svelte 5 runes-based device state management. */
import { apiClient, type DeviceState, type Catalog, type Snapshot, type ECUFull } from '$lib/api/client';

export interface ConnectionStatus {
  connected: boolean;
  port: string | null;
  message: string | null;
}

// ✅ Using Svelte 5 runes for reactive state (must be in .svelte.ts file)
class DeviceStore {
  // Reactive state using $state rune
  deviceState = $state<DeviceState | null>(null);
  catalog = $state<Catalog | null>(null);
  snapshots = $state<Snapshot[]>([]);
  isLoading = $state<boolean>(false);
  error = $state<string | null>(null);
  connectionStatus = $state<ConnectionStatus>({
    connected: false,
    port: null,
    message: null
  });
  selectedECUId = $state<string | null>(null);
  selectedECU = $state<ECUFull | null>(null);

  // ✅ Derived state using $derived rune
  ignitionState = $derived(this.deviceState?.ignition ?? false);
}

// Create singleton instance
const store = new DeviceStore();

// ✅ Export the store instance so components can access reactive state
// Components use: deviceStore.deviceState, deviceStore.catalog, etc.
export const deviceStore = store;

export async function fetchState(): Promise<void> {
  store.isLoading = true;
  store.error = null;
  try {
    const state = await apiClient.getState();
    store.deviceState = state;
  } catch (e) {
    store.error = e instanceof Error ? e.message : 'Failed to fetch state';
    console.error('Failed to fetch state:', e);
  } finally {
    store.isLoading = false;
  }
}

export async function updateState(updates: Partial<DeviceState>): Promise<void> {
  store.isLoading = true;
  store.error = null;
  try {
    // Filter out deprecated fields from potentiometer updates
    const filteredUpdates = { ...updates };
    if (filteredUpdates.potentiometers) {
      const cleanedPotentiometers: Record<string, any> = {};
      for (const [key, value] of Object.entries(filteredUpdates.potentiometers)) {
        const { application, wire_color, term_a_connect, term_b_connect, wiper_connect, ...rest } = value as any;
        cleanedPotentiometers[key] = rest;
      }
      filteredUpdates.potentiometers = cleanedPotentiometers;
    }
    
    const state = await apiClient.updateState(filteredUpdates);
    store.deviceState = state;
  } catch (e) {
    store.error = e instanceof Error ? e.message : 'Failed to update state';
    console.error('Failed to update state:', e);
    throw e;
  } finally {
    store.isLoading = false;
  }
}

export async function fetchCatalog(): Promise<void> {
  store.isLoading = true;
  store.error = null;
  try {
    const cat = await apiClient.getCatalog();
    store.catalog = cat;
  } catch (e) {
    store.error = e instanceof Error ? e.message : 'Failed to fetch catalog';
    console.error('Failed to fetch catalog:', e);
  } finally {
    store.isLoading = false;
  }
}

export async function fetchSnapshots(): Promise<void> {
  store.isLoading = true;
  store.error = null;
  try {
    const snaps = await apiClient.listSnapshots();
    store.snapshots = snaps;
  } catch (e) {
    store.error = e instanceof Error ? e.message : 'Failed to fetch snapshots';
    console.error('Failed to fetch snapshots:', e);
  } finally {
    store.isLoading = false;
  }
}

export async function saveSnapshot(label?: string): Promise<Snapshot> {
  store.isLoading = true;
  store.error = null;
  try {
    const snapshot = await apiClient.createSnapshot(label);
    await fetchSnapshots(); // Refresh list
    return snapshot;
  } catch (e) {
    store.error = e instanceof Error ? e.message : 'Failed to save snapshot';
    console.error('Failed to save snapshot:', e);
    throw e;
  } finally {
    store.isLoading = false;
  }
}

export async function revertToSnapshot(snapshotId: string): Promise<void> {
  store.isLoading = true;
  store.error = null;
  try {
    const state = await apiClient.revertSnapshot(snapshotId);
    store.deviceState = state;
    await fetchSnapshots(); // Refresh list
  } catch (e) {
    store.error = e instanceof Error ? e.message : 'Failed to revert snapshot';
    console.error('Failed to revert snapshot:', e);
    throw e;
  } finally {
    store.isLoading = false;
  }
}

export async function deleteSnapshot(snapshotId: string): Promise<void> {
  store.isLoading = true;
  store.error = null;
  try {
    await apiClient.deleteSnapshot(snapshotId);
    await fetchSnapshots(); // Refresh list
  } catch (e) {
    store.error = e instanceof Error ? e.message : 'Failed to delete snapshot';
    console.error('Failed to delete snapshot:', e);
    throw e;
  } finally {
    store.isLoading = false;
  }
}

export async function setSelectedECU(ecuId: string | null): Promise<void> {
  if (ecuId === null) {
    store.selectedECUId = null;
    store.selectedECU = null;
    // Clear from localStorage
    if (typeof window !== 'undefined') {
      localStorage.removeItem('selectedECUId');
    }
    return;
  }
  
  store.isLoading = true;
  store.error = null;
  try {
    const ecu = await apiClient.getECU(ecuId);
    store.selectedECUId = ecuId;
    store.selectedECU = ecu;
    // Save to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('selectedECUId', ecuId);
    }
  } catch (e) {
    store.error = e instanceof Error ? e.message : 'Failed to load ECU';
    console.error('Failed to load ECU:', e);
  } finally {
    store.isLoading = false;
  }
}

export function loadSelectedECUFromStorage(): void {
  if (typeof window !== 'undefined') {
    const storedECUId = localStorage.getItem('selectedECUId');
    if (storedECUId) {
      setSelectedECU(storedECUId);
    }
  }
}

export async function reloadSelectedECU(): Promise<void> {
  if (store.selectedECUId) {
    await setSelectedECU(store.selectedECUId);
  }
}
