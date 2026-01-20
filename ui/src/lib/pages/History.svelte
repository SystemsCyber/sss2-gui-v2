<script lang="ts">
  import { deviceStore, revertToSnapshot, deleteSnapshot } from '$lib/stores/deviceStore.svelte';

  // ✅ Using $derived rune for reactive value
  const snapshots = $derived(deviceStore.snapshots);

  async function handleRevert(snapshotId: string) {
    if (!confirm('Are you sure you want to revert to this snapshot? This will overwrite your current settings.')) {
      return;
    }

    try {
      await revertToSnapshot(snapshotId);
    } catch (error) {
      console.error('Failed to revert snapshot:', error);
      alert('Failed to revert snapshot. Please try again.');
    }
  }

  async function handleDelete(snapshotId: string) {
    if (!confirm('Are you sure you want to delete this snapshot? This action cannot be undone.')) {
      return;
    }

    try {
      await deleteSnapshot(snapshotId);
    } catch (error) {
      console.error('Failed to delete snapshot:', error);
      alert('Failed to delete snapshot. Please try again.');
    }
  }
</script>

<div class="max-w-7xl mx-auto space-y-6">
  <div>
    <h2 class="text-2xl font-bold mb-2">History</h2>
    <p class="text-gray-400">Manage snapshots</p>
  </div>

  {#if snapshots.length === 0}
    <div class="bg-dark-card rounded-lg p-12 text-center">
      <p class="text-gray-400 text-lg">No snapshots</p>
      <p class="text-gray-500 text-sm mt-2">Create snapshots from the Dashboard</p>
    </div>
  {:else}
    <div class="space-y-2">
      {#each snapshots as snapshot (snapshot.id)}
        <div class="bg-dark-card rounded-lg p-4 flex items-center justify-between border border-dark-accent/20">
          <div>
            <div class="font-semibold">{snapshot.label || 'Unnamed Snapshot'}</div>
            <div class="text-sm text-gray-400">{snapshot.created_at}</div>
          </div>
          <div class="flex gap-2">
            <button
              class="px-4 py-2 rounded bg-orange-600 hover:bg-orange-700 transition-colors min-h-touch"
              onclick={() => handleRevert(snapshot.id)}
            >
              Revert
            </button>
            <button
              class="px-4 py-2 rounded bg-red-600 hover:bg-red-700 transition-colors min-h-touch"
              onclick={() => handleDelete(snapshot.id)}
            >
              Delete
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
