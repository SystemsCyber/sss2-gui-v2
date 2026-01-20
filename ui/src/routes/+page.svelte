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

  type Route = 'dashboard' | 'settings' | 'history';

  let currentRoute = $state<Route>('dashboard');
  let unsubscribe: (() => void) | null = null;

  // ✅ Derived values using $derived rune
  const connectionStatus = $derived(deviceStore.connectionStatus);

  onMount(() => {
    // Load initial data
    fetchState();
    fetchCatalog();
    fetchSnapshots();

    // Connect WebSocket for connection status updates
    const wsClient = connectWebSocket();
    unsubscribe = wsClient.subscribe((message: ConnectionStatusMessage) => {
      // ✅ Update connectionStatus directly (rune-based)
      deviceStore.connectionStatus = {
        connected: message.connected,
        port: message.port,
        message: message.message
      };
      
      // ✅ Update deviceState connection status directly
      if (deviceStore.deviceState) {
        deviceStore.deviceState.connected_port = message.connected ? message.port : null;
      }
    });
  });

  onDestroy(() => {
    // Cleanup WebSocket connection
    if (unsubscribe) {
      unsubscribe();
    }
    disconnectWebSocket();
  });

  function navigate(route: Route) {
    currentRoute = route;
  }
</script>

<div class="min-h-screen bg-dark-bg text-white">
  <!-- Top Navigation -->
  <nav class="bg-dark-surface border-b border-dark-card">
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

  <!-- Main Content -->
  <main class="p-4 pb-20">
    {#if currentRoute === 'dashboard'}
      <Dashboard />
    {:else if currentRoute === 'settings'}
      <Settings />
    {:else if currentRoute === 'history'}
      <History />
    {/if}
  </main>

  <!-- Fixed Bottom Footer -->
  <footer class="fixed bottom-0 left-0 right-0 bg-dark-surface border-t border-dark-card px-4 py-2">
    <div class="flex justify-end">
      <div class="text-sm text-gray-400">
        Connection: {#if connectionStatus.connected}
          <span class="text-green-400">Connected {#if connectionStatus.port}({connectionStatus.port}){/if}</span>
        {:else}
          <span class="text-red-400">Disconnected</span>
        {/if}
      </div>
    </div>
  </footer>

  <!-- Connection Notification (modalless) -->
  <ConnectionNotification />
</div>
