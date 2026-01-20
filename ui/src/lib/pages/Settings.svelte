<script lang="ts">
  import { deviceStore } from '$lib/stores/deviceStore.svelte';
  import PotentiometerCard from '$lib/components/PotentiometerCard.svelte';
  import type { PotentiometerDefinition } from '$lib/api/client';

  type Tab = 'potentiometers' | 'vouts' | 'pwm' | 'can' | 'j1708';
  let activeTab = $state<Tab>('potentiometers');

  // ✅ Using $derived rune for reactive value
  const potentiometers = $derived(deviceStore.catalog?.potentiometers ?? []);
</script>

<div class="max-w-7xl mx-auto space-y-6">
  <div>
    <h2 class="text-2xl font-bold mb-2">Settings</h2>
    <p class="text-gray-400">Configure potentiometers & dashboard</p>
  </div>

  <!-- Tabs -->
  <div class="flex gap-2 border-b border-dark-accent/20">
    <button
      class="px-6 py-3 font-semibold border-b-2 transition-colors min-h-touch"
      class:border-dark-accent={activeTab === 'potentiometers'}
      class:text-dark-accent={activeTab === 'potentiometers'}
      class:border-transparent={activeTab !== 'potentiometers'}
      onclick={() => activeTab = 'potentiometers'}
    >
      Potentiometers
    </button>
    <button
      class="px-6 py-3 font-semibold border-b-2 transition-colors min-h-touch opacity-50"
      disabled
    >
      VOUTs (Coming soon)
    </button>
    <button
      class="px-6 py-3 font-semibold border-b-2 transition-colors min-h-touch opacity-50"
      disabled
    >
      PWM (Coming soon)
    </button>
    <button
      class="px-6 py-3 font-semibold border-b-2 transition-colors min-h-touch opacity-50"
      disabled
    >
      CAN (Coming soon)
    </button>
    <button
      class="px-6 py-3 font-semibold border-b-2 transition-colors min-h-touch opacity-50"
      disabled
    >
      J1708 (Coming soon)
    </button>
  </div>

  <!-- Content -->
  <div class="space-y-4">
    {#if activeTab === 'potentiometers'}
      {#each potentiometers as pot (pot.id)}
        <PotentiometerCard potDef={pot} />
      {/each}
    {:else if activeTab === 'vouts'}
      <p class="text-gray-400">VOUTs configuration coming soon</p>
    {:else if activeTab === 'pwm'}
      <p class="text-gray-400">PWM configuration coming soon</p>
    {:else if activeTab === 'can'}
      <p class="text-gray-400">CAN configuration coming soon</p>
    {:else if activeTab === 'j1708'}
      <p class="text-gray-400">J1708 configuration coming soon</p>
    {/if}
  </div>
</div>
