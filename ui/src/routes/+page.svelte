<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { deviceStore, fetchState, fetchCatalog, fetchSnapshots } from '$lib/stores/deviceStore.svelte';
  import { connectWebSocket, disconnectWebSocket, type ConnectionStatusMessage } from '$lib/api/wsClient';
  import Dashboard from '$lib/pages/Dashboard.svelte';
  import Settings from '$lib/pages/Settings.svelte';
  import History from '$lib/pages/History.svelte';
  import IgnitionToggle from '$lib/components/IgnitionToggle.svelte';
  import SnapshotControls from '$lib/components/SnapshotControls.svelte';
  import ConnectionNotification from '$lib/components/ConnectionNotification.svelte';
  import SerialConnectionModal from '$lib/components/SerialConnectionModal.svelte';
  import ECUSelector from '$lib/components/ECUSelector.svelte';

  type Route = 'dashboard' | 'settings' | 'history';

  let currentRoute = $state<Route>('dashboard');
  let unsubscribe: (() => void) | null = null;
  let pollInterval: ReturnType<typeof setInterval> | null = null;

  // ✅ Derived values using $derived rune
  const connectionStatus = $derived(deviceStore.connectionStatus);
  
  // Load selected ECU from localStorage on mount
  import { loadSelectedECUFromStorage } from '$lib/stores/deviceStore.svelte';

  // Fetch connection status via REST API
  async function fetchConnectionStatus() {
    try {
      const response = await fetch('/api/connection/status');
      if (response.ok) {
        const status = await response.json();
        console.log('Fetched connection status via REST:', status);
        deviceStore.connectionStatus = {
          connected: status.connected,
          port: status.port || null,
          message: status.message
        };
      }
    } catch (error) {
      console.error('Failed to fetch connection status:', error);
    }
  }

  onMount(() => {
    // Load initial data
    fetchState();
    fetchCatalog();
    fetchSnapshots();
    loadSelectedECUFromStorage();

    // Fetch initial status via REST API
    fetchConnectionStatus();

    // Connect WebSocket for connection status updates
    const wsClient = connectWebSocket();
    unsubscribe = wsClient.subscribe((message: ConnectionStatusMessage) => {
      // Only log if status actually changed (reduce noise)
      const prevStatus = deviceStore.connectionStatus.connected;
      const newStatus = message.connected;
      
      if (prevStatus !== newStatus) {
        console.log('Connection status changed:', message);
      }
      
      // ✅ Update connectionStatus directly (rune-based)
      deviceStore.connectionStatus = {
        connected: message.connected,
        port: message.port || null,
        message: message.message
      };
      
      // ✅ Update deviceState connection status directly
      if (deviceStore.deviceState) {
        deviceStore.deviceState.connected_port = message.connected ? message.port : null;
      }
      
      // When connection is established, fetch latest state from backend (source of truth)
      if (!prevStatus && newStatus) {
        console.log('Connection established - fetching latest state from backend');
        fetchState();
      }
    });
    
    // Fallback: Poll connection status every 5 seconds if WebSocket might not be working
    pollInterval = setInterval(() => {
      // Only poll if we haven't received a recent update (check if message is null)
      if (deviceStore.connectionStatus.message === null) {
        fetchConnectionStatus();
      }
    }, 5000);
  });

  onDestroy(() => {
    // Cleanup WebSocket connection
    if (unsubscribe) {
      unsubscribe();
    }
    disconnectWebSocket();
    
    // Cleanup polling interval
    if (pollInterval) {
      clearInterval(pollInterval);
    }
  });

  function navigate(route: Route) {
    currentRoute = route;
  }
</script>

<div class="min-h-screen bg-dark-bg text-white">
  <!-- Fixed Top Navigation -->
  <nav class="fixed top-0 left-0 right-0 z-[100] bg-[#103f03] border-b border-dark-card">
    <div class="flex items-center justify-between px-4 py-3">
      <h1 class="text-xl font-bold">Smart Sensor Simulation 2 (SSS2)</h1>
      <div class="flex items-center gap-4">
        <button
          class="px-4 py-2 rounded bg-dark-card hover:bg-dark-accent transition-colors min-h-touch"
          onclick={() => navigate('dashboard')}
        >
          Dashboard
        </button>
        <SnapshotControls />
        <ECUSelector />
        <button
          class="px-4 py-2 rounded bg-dark-card hover:bg-dark-accent transition-colors min-h-touch"
          onclick={() => navigate('settings')}
        >
          Settings
        </button>
        <button
          class="px-4 py-2 rounded bg-dark-card hover:bg-dark-accent transition-colors min-h-touch"
          onclick={() => navigate('history')}
        >
          History
        </button>
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-400">Ignition</span>
          <IgnitionToggle />
        </div>
      </div>
    </div>
  </nav>

  <!-- Main Content - scrolls behind header and footer -->
  <main class="relative z-0 pt-20 pb-20 px-4">
    {#if currentRoute === 'dashboard'}
      <Dashboard />
    {:else if currentRoute === 'settings'}
      <Settings />
    {:else if currentRoute === 'history'}
      <History />
    {/if}
  </main>

  <!-- Fixed Bottom Footer -->
  <footer class="fixed bottom-0 left-0 right-0 z-[100] bg-[#0a2338] border-t border-dark-card px-4 py-2">
    <div class="flex justify-end">
      <div class="text-sm text-gray-400">
        Serial Connection: {#if connectionStatus.connected}
          <span class="text-green-400">Connected</span>
        {:else}
          <span class="text-red-400">Disconnected</span>
        {/if}
      </div>
    </div>
  </footer>

  <!-- Connection Notification (modalless) -->
  <ConnectionNotification />
  
  <!-- Serial Connection Modal (blocks interaction when disconnected) -->
  <SerialConnectionModal />
</div>
