<script lang="ts">
  import { deviceStore } from '$lib/stores/deviceStore.svelte';
  
  // ✅ Using $derived runes for reactive values
  const connectionStatus = $derived(deviceStore.connectionStatus);
  
  // Only show modal if:
  // 1. We've received a status update from backend (message is not null)
  // 2. AND the connection is actually disconnected
  // This prevents showing modal during initial page load before WebSocket connects
  const isVisible = $derived(
    connectionStatus.message !== null && !connectionStatus.connected
  );
  const statusMessage = $derived(connectionStatus.message || 'No serial communication available');
  const port = $derived(connectionStatus.port);
</script>

{#if isVisible}
  <!-- Backdrop with dimmed background - blocks all interactions -->
  <div
    class="fixed inset-0 bg-black/60 z-[100] flex items-center justify-center pointer-events-auto"
    role="dialog"
    aria-modal="true"
    aria-labelledby="modal-title"
    aria-describedby="modal-description"
  >
    <!-- Modal Dialog -->
    <div class="bg-dark-surface border-2 border-red-500 rounded-lg shadow-2xl p-8 max-w-md mx-4 pointer-events-auto">
      <div class="flex flex-col items-center gap-4">
        <!-- Warning Icon -->
        <div class="flex-shrink-0">
          <svg
            class="w-16 h-16 text-red-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        
        <!-- Title -->
        <h2 id="modal-title" class="text-2xl font-bold text-white text-center">
          Serial Connection Lost
        </h2>
        
        <!-- Message -->
        <p id="modal-description" class="text-gray-300 text-center">
          {statusMessage}
        </p>
        
        {#if port}
          <p class="text-sm text-gray-400 text-center">
            Port: {port}
          </p>
        {/if}
        
        <!-- Status Indicator -->
        <div class="flex items-center gap-2 mt-2">
          <div class="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
          <span class="text-sm text-gray-400">Waiting for connection...</span>
        </div>
      </div>
    </div>
  </div>
{/if}
