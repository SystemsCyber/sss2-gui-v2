<script lang="ts">
  import { deviceStore, saveSnapshot, revertToSnapshot } from '$lib/stores/deviceStore.svelte';

  let selectedSnapshotId = $state<string | null>(null);
  let isSaving = $state(false);

  // ✅ Using $derived rune for reactive value
  const snapshots = $derived(deviceStore.snapshots);

  async function handleSave() {
    if (isSaving) return;
    isSaving = true;
    try {
      await saveSnapshot();
      selectedSnapshotId = null; // Clear selection after save
    } catch (error) {
      console.error('Failed to save snapshot:', error);
      alert('Failed to save snapshot. Please try again.');
    } finally {
      isSaving = false;
    }
  }

  async function handleRevert() {
    if (!selectedSnapshotId) return;
    
    if (!confirm('Are you sure you want to revert to this snapshot? This will overwrite your current settings.')) {
      return;
    }

    try {
      await revertToSnapshot(selectedSnapshotId);
      selectedSnapshotId = null; // Clear selection after revert
    } catch (error) {
      console.error('Failed to revert snapshot:', error);
      alert('Failed to revert snapshot. Please try again.');
    }
  }
</script>

<div class="flex flex-col gap-2">
  <div class="flex gap-2 items-center">
    <button
      class="px-4 py-2 rounded bg-dark-accent hover:bg-dark-accent/80 transition-colors min-h-touch"
      onclick={handleSave}
      disabled={isSaving}
    >
      {isSaving ? 'Saving...' : 'Save Snapshot'}
    </button>

    <select
      class="px-4 py-2 rounded bg-dark-card border border-dark-accent min-h-touch flex-1"
      bind:value={selectedSnapshotId}
    >
      <option value={null}>Select a snapshot...</option>
      {#each snapshots as snapshot (snapshot.id)}
        <option value={snapshot.id}>{snapshot.label || snapshot.created_at}</option>
      {/each}
    </select>

    <button
      class="px-4 py-2 rounded bg-orange-600 hover:bg-orange-700 transition-colors min-h-touch disabled:opacity-50 disabled:cursor-not-allowed"
      onclick={handleRevert}
      disabled={!selectedSnapshotId}
    >
      Revert
    </button>
  </div>
</div>
