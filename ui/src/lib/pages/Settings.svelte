<script lang="ts">
  import { deviceStore } from '$lib/stores/deviceStore.svelte';
  import PotentiometerGroup from '$lib/components/PotentiometerGroup.svelte';
  import ECUList from '$lib/components/ECUList.svelte';
  import type { PotentiometerDefinition } from '$lib/api/client';

  type Tab = 'potentiometers' | 'vouts' | 'pwm' | 'can' | 'j1708' | 'ecu';
  let activeTab = $state<Tab>('potentiometers');

  // ✅ Using $derived rune for reactive value
  const potentiometers = $derived(deviceStore.catalog?.potentiometers ?? []);
  
  // Group potentiometers into pairs
  const potentiometerGroups = $derived(() => {
    const groups: Array<{ groupId: number; pot1: PotentiometerDefinition; pot2: PotentiometerDefinition }> = [];
    
    // Group 1-2: po1, po2
    const pot1 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po1');
    const pot2 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po2');
    if (pot1 && pot2) groups.push({ groupId: 1, pot1, pot2 });
    
    // Group 3-4: po3, po4
    const pot3 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po3');
    const pot4 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po4');
    if (pot3 && pot4) groups.push({ groupId: 2, pot1: pot3, pot2: pot4 });
    
    // Group 5-6: po5, po6
    const pot5 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po5');
    const pot6 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po6');
    if (pot5 && pot6) groups.push({ groupId: 3, pot1: pot5, pot2: pot6 });
    
    // Group 7-8: po7, po8
    const pot7 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po7');
    const pot8 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po8');
    if (pot7 && pot8) groups.push({ groupId: 4, pot1: pot7, pot2: pot8 });
    
    // Group 9-10: po9, po10
    const pot9 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po9');
    const pot10 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po10');
    if (pot9 && pot10) groups.push({ groupId: 5, pot1: pot9, pot2: pot10 });
    
    // Group 11-12: po11, po12
    const pot11 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po11');
    const pot12 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po12');
    if (pot11 && pot12) groups.push({ groupId: 6, pot1: pot11, pot2: pot12 });
    
    // Group 13-14: po13, po14
    const pot13 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po13');
    const pot14 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po14');
    if (pot13 && pot14) groups.push({ groupId: 7, pot1: pot13, pot2: pot14 });
    
    // Group 15-16: po15, po16
    const pot15 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po15');
    const pot16 = potentiometers.find((p: PotentiometerDefinition) => p.id === 'po16');
    if (pot15 && pot16) groups.push({ groupId: 8, pot1: pot15, pot2: pot16 });
    
    return groups;
  });
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
    <button
      class="px-6 py-3 font-semibold border-b-2 transition-colors min-h-touch"
      class:border-dark-accent={activeTab === 'ecu'}
      class:text-dark-accent={activeTab === 'ecu'}
      class:border-transparent={activeTab !== 'ecu'}
      onclick={() => activeTab = 'ecu'}
    >
      ECU Functions
    </button>
  </div>

  <!-- Content -->
  <div class="space-y-4">
    {#if activeTab === 'potentiometers'}
      {#each potentiometerGroups() as group (group.groupId)}
        <PotentiometerGroup pot1={group.pot1} pot2={group.pot2} groupId={group.groupId} />
      {/each}
    {:else if activeTab === 'vouts'}
      <p class="text-gray-400">VOUTs configuration coming soon</p>
    {:else if activeTab === 'pwm'}
      <p class="text-gray-400">PWM configuration coming soon</p>
    {:else if activeTab === 'can'}
      <p class="text-gray-400">CAN configuration coming soon</p>
    {:else if activeTab === 'j1708'}
      <p class="text-gray-400">J1708 configuration coming soon</p>
    {:else if activeTab === 'ecu'}
      <ECUList />
    {/if}
  </div>
</div>
