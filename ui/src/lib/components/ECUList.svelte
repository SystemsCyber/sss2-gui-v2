<script lang="ts">
  import { onMount } from 'svelte';
  import { apiClient, type ECUItem } from '$lib/api/client';
  import ECUForm from './ECUForm.svelte';
  import ECUDetails from './ECUDetails.svelte';
  
  let ecus = $state<ECUItem[]>([]);
  let selectedECUId = $state<string | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);
  
  // Define all available pins based on the schematic
  const j24Pins = Array.from({ length: 24 }, (_, i) => `J24:${i + 1}`);
  const j18Pins = Array.from({ length: 18 }, (_, i) => `J18:${i + 1}`);
  const allPins = [...j24Pins, ...j18Pins];
  
  let showAddModal = $state(false);
  let showEditModal = $state(false);
  let ecuToEdit = $state<ECUItem | null>(null);
  let showDeleteConfirm = $state(false);
  let ecuToDelete = $state<string | null>(null);
  
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
  
  function handleAddNew() {
    showAddModal = true;
  }
  
  function handleEdit(ecu: ECUItem) {
    ecuToEdit = ecu;
    showEditModal = true;
  }
  
  function handleDelete(ecuId: string) {
    ecuToDelete = ecuId;
    showDeleteConfirm = true;
  }
  
  async function confirmDelete() {
    if (!ecuToDelete) return;
    
    try {
      await apiClient.deleteECU(ecuToDelete);
      await loadECUs();
      if (selectedECUId === ecuToDelete) {
        selectedECUId = null;
      }
      showDeleteConfirm = false;
      ecuToDelete = null;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to delete ECU';
      console.error('Failed to delete ECU:', err);
    }
  }
  
  function closeModals() {
    showAddModal = false;
    showEditModal = false;
    showDeleteConfirm = false;
    ecuToEdit = null;
    ecuToDelete = null;
  }
  
  function handleECUSaved() {
    closeModals();
    loadECUs();
  }
  
  // Load ECUs on mount
  onMount(() => {
    loadECUs();
  });
</script>

<div class="space-y-4">
  <!-- Header with Add Button -->
  <div class="flex items-center justify-between">
    <h3 class="text-xl font-semibold">ECU Configurations</h3>
    <button
      class="px-6 py-3 rounded bg-dark-accent hover:bg-dark-accent/80 text-dark-bg font-semibold transition-colors min-h-touch"
      onclick={handleAddNew}
    >
      + Add New ECU
    </button>
  </div>
  
  {#if error}
    <div class="p-4 rounded bg-red-900/30 border border-red-500 text-red-200">
      {error}
    </div>
  {/if}
  
  {#if loading}
    <div class="text-center py-8 text-gray-400">Loading ECUs...</div>
  {:else if ecus.length === 0}
    <div class="text-center py-8 text-gray-400">
      <p class="mb-4">No ECU configurations found.</p>
      <button
        class="px-6 py-3 rounded bg-dark-accent hover:bg-dark-accent/80 text-dark-bg font-semibold transition-colors min-h-touch"
        onclick={handleAddNew}
      >
        Add Your First ECU
      </button>
    </div>
  {:else}
    <!-- ECU List -->
    <div class="space-y-2">
      {#each ecus as ecu (ecu.id)}
        <div
          class="bg-dark-card rounded-lg border border-dark-accent/20 p-4 flex items-center justify-between hover:bg-dark-surface/50 transition-colors"
          class:border-dark-accent={selectedECUId === ecu.id}
          class:border-2={selectedECUId === ecu.id}
        >
          <button
            class="flex-1 text-left"
            onclick={() => selectedECUId = selectedECUId === ecu.id ? null : ecu.id}
          >
            <div class="font-semibold text-lg">{ecu.name}</div>
            {#if ecu.model}
              <div class="text-sm text-gray-400">Model: {ecu.model}</div>
            {/if}
            {#if ecu.serial_number}
              <div class="text-sm text-gray-400">Serial: {ecu.serial_number}</div>
            {/if}
          </button>
          <div class="flex gap-2 ml-4">
            <button
              class="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white font-semibold transition-colors min-h-touch"
              onclick={() => handleEdit(ecu)}
            >
              Edit
            </button>
            <button
              class="px-4 py-2 rounded bg-red-600 hover:bg-red-700 text-white font-semibold transition-colors min-h-touch"
              onclick={() => handleDelete(ecu.id)}
            >
              Delete
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
  
  <!-- ECU Selection View -->
  {#if selectedECUId}
    <ECUDetails ecuId={selectedECUId} />
  {/if}
  
  <!-- Add Modal -->
  {#if showAddModal}
    <ECUForm onSave={handleECUSaved} onCancel={closeModals} allPins={allPins} />
  {/if}
  
  <!-- Edit Modal -->
  {#if showEditModal && ecuToEdit}
    <ECUForm ecuId={ecuToEdit.id} onSave={handleECUSaved} onCancel={closeModals} allPins={allPins} />
  {/if}
  
  <!-- Delete Confirmation Modal -->
  {#if showDeleteConfirm && ecuToDelete}
    <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" role="dialog" aria-modal="true" onclick={closeModals} onkeydown={(e) => e.key === 'Escape' && closeModals()}>
      <div class="bg-dark-card rounded-lg border border-dark-accent/20 p-6 max-w-md w-full mx-4" onclick={(e) => e.stopPropagation()} role="document">
        <h3 class="text-xl font-semibold mb-4">Delete ECU</h3>
        <p class="text-gray-300 mb-6">
          Are you sure you want to delete this ECU configuration? This action cannot be undone.
        </p>
        <div class="flex gap-4 justify-end">
          <button
            class="px-6 py-3 rounded bg-dark-surface hover:bg-dark-surface/80 text-white font-semibold transition-colors min-h-touch"
            onclick={closeModals}
          >
            Cancel
          </button>
          <button
            class="px-6 py-3 rounded bg-red-600 hover:bg-red-700 text-white font-semibold transition-colors min-h-touch"
            onclick={confirmDelete}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>
