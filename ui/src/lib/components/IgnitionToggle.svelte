<script lang="ts">
  import { deviceStore, fetchState } from '$lib/stores/deviceStore.svelte';
  import { apiClient } from '$lib/api/client';

  let isToggling = $state(false);

  const currentIgnition = $derived(deviceStore.ignitionState);
  const displayText = $derived(isToggling ? '...' : (currentIgnition ? 'Start' : 'OFF'));
  const isOnClass = $derived(currentIgnition && !isToggling);
  const isOffClass = $derived(!currentIgnition && !isToggling);

  async function toggle(event: MouseEvent) {
    event.preventDefault();
    event.stopPropagation();

    if (isToggling) { return; }

    const currentState = currentIgnition;
    const newState = !currentState;

    isToggling = true;

    try {
      const response = await apiClient.setIgnition(newState);

      if (response.accepted && response.executed) {
        const serverIgnition = !!response.ignition;

        // Update deviceState directly (rune-based mutation)
        if (deviceStore.deviceState) {
          deviceStore.deviceState.ignition = serverIgnition;
          deviceStore.deviceState.last_updated = new Date().toISOString();
        } else {
          deviceStore.deviceState = {
            sss2_version: null,
            last_updated: new Date().toISOString(),
            connected_port: null,
            ignition: serverIgnition,
            potentiometers: {},
            vouts: {},
            pwms: {},
            can: {},
            j1708: {}
          };
        }

        // Refresh state from server
        await fetchState();

      } else if (response.accepted && !response.executed) {
        alert(`Warning: ${response.detail}`);
      } else {
        alert(`Error: ${response.detail}`);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to toggle ignition. Please try again.';
      alert(errorMessage);
    } finally {
      isToggling = false;
    }
  }
</script>

<button
  class={`ignition-toggle-button relative overflow-hidden font-bold text-lg min-h-touch transition-all ${
    isToggling ? 'cursor-not-allowed' : 'cursor-pointer hover:opacity-90'
  }`}
  class:is-on={isOnClass}
  class:is-off={isOffClass}
  class:is-toggling={isToggling}
  onclick={toggle}
  disabled={isToggling}
>
  <div class="flex items-center justify-center gap-2 px-6 py-3">
    <!-- Power Icon SVG - Circle with vertical line on top -->
    <svg
  class="w-5 h-5"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2.5"
  stroke-linecap="round"
  stroke-linejoin="round"
  aria-hidden="true"
>
  <!-- Vertical line -->
  <path d="M12 3v7" />

  <!-- Broken circle (gap at top) -->
  <path d="M7.05 6.55a8 8 0 1 0 9.9 0" />
</svg>
    <span class="uppercase">{displayText}</span>
  </div>
</button>

<style>
  .ignition-toggle-button {
    border-radius: 0.5rem;
    min-width: 120px;
    border: 1px solid;
    transition: all 0.2s ease;
  }

  .ignition-toggle-button.is-on {
    background-color: #0f4c3a; /* dark teal/deep green */
    border-color: #84cc16; /* bright lime green */
    color: #84cc16; /* bright lime green for icon and text */
  }

  .ignition-toggle-button.is-on:hover:not(:disabled) {
    background-color: #134e3a;
    border-color: #a3e635;
    color: #a3e635;
  }

  .ignition-toggle-button.is-off {
    background-color: #7c2d12; /* dark reddish-purple/maroon */
    border-color: #d1d5db; /* light gray/off-white */
    color: #fb7185; /* lighter coral-red for icon and text */
  }

  .ignition-toggle-button.is-off:hover:not(:disabled) {
    background-color: #9a3412;
    border-color: #e5e7eb;
    color: #fda4af;
  }

  .ignition-toggle-button.is-toggling {
    opacity: 0.7;
    background-color: #6b7280; /* gray-500 */
    border-color: #9ca3af;
    color: #d1d5db;
  }

  .ignition-toggle-button:disabled {
    cursor: not-allowed;
  }
</style>
