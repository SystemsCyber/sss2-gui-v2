<script lang="ts">
  import { onMount } from 'svelte';
  import { apiClient, type ECUItem } from '$lib/api/client';
  import { deviceStore, setSelectedECU } from '$lib/stores/deviceStore.svelte';
  
  let ecus = $state<ECUItem[]>([]);
  let loading = $state(false);
  let error = $state<string | null>(null);
  
  // Derived selected ECU ID from store
  const selectedECUId = $derived(deviceStore.selectedECUId);
  
  async function loadECUs() {
    loading = true;
    error = null;
    try {
      ecus = await apiClient.listECUs();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load ECUs';
      console.error('Failed to load ECUs:', err);
    } finally {
      loading = false;
    }
  }
  
  function handleECUChange(event: Event) {
    const selectElement = event.currentTarget as HTMLSelectElement;
    const ecuId = selectElement.value || null;
    setSelectedECU(ecuId);
  }
  
  onMount(() => {
    loadECUs();
  });
</script>

<div class="flex items-center gap-2">
  <label for="ecu-selector" class="text-sm text-gray-300 whitespace-nowrap">ECU:</label>
  <select
    id="ecu-selector"
    value={selectedECUId || ''}
    onchange={handleECUChange}
    class="px-4 py-2 rounded bg-dark-card border border-dark-accent/20 focus:border-dark-accent focus:outline-none text-white min-h-touch min-w-[200px]"
    disabled={loading}
  >
    <option value="">No ECU Selected</option>
    {#each ecus as ecu (ecu.id)}
      <option value={ecu.id}>{ecu.name}</option>
    {/each}
  </select>
  {#if loading}
    <span class="text-xs text-gray-400">Loading...</span>
  {/if}
</div>
