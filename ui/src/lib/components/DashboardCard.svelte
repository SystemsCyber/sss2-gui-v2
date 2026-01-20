<script lang="ts">
  // ✅ Using $props() rune for component props (Svelte 5)
  let { title, count = 0, comingSoon = false }: { title: string; count?: number; comingSoon?: boolean } = $props();
</script>

<div class="bg-dark-card rounded-lg p-6 border border-dark-accent/20">
  <h3 class="text-xl font-semibold mb-2">{title}</h3>
  {#if comingSoon}
    <p class="text-gray-400">Coming soon</p>
  {/if}
  <p class="text-2xl font-bold text-dark-accent">{count}</p>
</div>
