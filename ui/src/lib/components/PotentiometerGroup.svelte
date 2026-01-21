<script lang="ts">
  import { onMount } from 'svelte';
  import type { PotentiometerDefinition, PotentiometerPowerGroup } from '$lib/api/client';
  import { deviceStore, updateState } from '$lib/stores/deviceStore.svelte';
  import PotentiometerCard from './PotentiometerCard.svelte';
  
  interface Props {
    pot1: PotentiometerDefinition;
    pot2: PotentiometerDefinition;
    groupId: number;  // 1-8 (1=pot1-2, 2=pot3-4, etc.)
  }
  
  let { pot1, pot2, groupId }: Props = $props();
  
  // Get power group state
  const groupKey = $derived(`group_${groupId}`);
  const powerGroup = $derived(
    deviceStore.deviceState?.potentiometer_power_groups?.[groupKey] as PotentiometerPowerGroup | undefined
  );
  
  // Default to 5V if not set
  const voltageSetting = $derived(powerGroup?.voltage_setting ?? '5V');
  
  async function updatePowerSetting(setting: '5V' | '12V') {
    if (voltageSetting === setting) return;
    
    try {
      await updateState({
        potentiometer_power_groups: {
          [groupKey]: {
            group_id: groupKey,
            voltage_setting: setting,
            potentiometers: [pot1.id, pot2.id]
          }
        }
      });
    } catch (error) {
      console.error('Failed to update power setting:', error);
      alert('Failed to update power setting. Please try again.');
    }
  }
</script>

<div class="bg-dark-card rounded-lg border border-dark-accent/20 p-6 space-y-4">
  <!-- Power Selection -->
  <div class="flex items-center gap-6 pb-4 border-b border-dark-accent/20">
    <span class="text-sm font-semibold text-gray-300">Power Setting:</span>
    <div class="flex gap-4">
      <label class="flex items-center gap-2 cursor-pointer min-h-touch">
        <input
          type="radio"
          name="power-{groupId}"
          value="5V"
          checked={voltageSetting === '5V'}
          onchange={() => updatePowerSetting('5V')}
          class="w-6 h-6 accent-dark-accent"
        />
        <span class="text-lg font-semibold">+5V</span>
      </label>
      <label class="flex items-center gap-2 cursor-pointer min-h-touch">
        <input
          type="radio"
          name="power-{groupId}"
          value="12V"
          checked={voltageSetting === '12V'}
          onchange={() => updatePowerSetting('12V')}
          class="w-6 h-6 accent-dark-accent"
        />
        <span class="text-lg font-semibold">+12V</span>
      </label>
    </div>
  </div>
  
  <!-- Potentiometers -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <PotentiometerCard potDef={pot1} powerVoltage={voltageSetting} />
    <PotentiometerCard potDef={pot2} powerVoltage={voltageSetting} />
  </div>
</div>
