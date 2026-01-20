<script lang="ts">
  import { deviceStore } from '$lib/stores/deviceStore.svelte';
  import DashboardCard from '$lib/components/DashboardCard.svelte';

  // ✅ Using $derived rune for reactive value
  const potCount = $derived(deviceStore.catalog?.potentiometers?.length ?? 0);
</script>

<div class="max-w-7xl mx-auto space-y-6">

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <DashboardCard title="Potentiometers" count={potCount} />
    <DashboardCard title="VOUTs" count={0} comingSoon={true} />
    <DashboardCard title="PWMs" count={0} comingSoon={true} />
    <DashboardCard title="CAN" count={0} comingSoon={true} />
    <DashboardCard title="J1708" count={0} comingSoon={true} />
  </div>
</div>
