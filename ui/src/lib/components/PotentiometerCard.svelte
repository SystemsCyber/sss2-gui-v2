<script lang="ts">
  import { onDestroy } from 'svelte';
  import type { PotentiometerDefinition, PotentiometerState } from '$lib/api/client';
  import { deviceStore, updateState } from '$lib/stores/deviceStore.svelte';

  // ✅ Using $props() rune for component props (Svelte 5)
  let { potDef, powerVoltage = '5V' }: { potDef: PotentiometerDefinition; powerVoltage?: '5V' | '12V' } = $props();
  
  let expanded = $state(false);
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;
  let localWiperPosition = $state<number | null>(null);
  
  // ✅ Using $derived rune for reactive state
  const potState = $derived(deviceStore.deviceState?.potentiometers?.[potDef.id] as PotentiometerState | undefined);
  
  // Use local state for slider if available, otherwise use potState
  const displayWiperPosition = $derived(localWiperPosition ?? potState?.wiper_position ?? 0);
  
  // Get ECU pin configuration for this potentiometer's pin
  const ecuPinConfig = $derived(
    deviceStore.selectedECU?.pins?.[potDef.pin] || null
  );

  async function updatePot(updates: Partial<PotentiometerState>, debounce: boolean = false) {
    if (!potState) return;
    
    // Filter out application, wire_color, and old terminal fields from updates
    const { application, wire_color, term_a_connect, term_b_connect, wiper_connect, ...filteredUpdates } = updates as any;
    
    // If debouncing, clear previous timer and set new one
    if (debounce) {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
      
      debounceTimer = setTimeout(async () => {
        try {
          await updateState({
            potentiometers: {
              [potDef.id]: {
                ...potState,
                ...filteredUpdates
              }
            }
          });
          // Clear local state after successful update
          localWiperPosition = null;
        } catch (error) {
          // Silently handle timeout errors during slider movement
          // State is saved, hardware command is sent in background
          if (error instanceof Error && error.message.includes('timeout')) {
            console.log(`Potentiometer ${potDef.id} command queued (may timeout, but state saved)`);
          } else {
            console.error('Failed to update potentiometer:', error);
            // Only show alert for non-timeout errors
            alert('Failed to update potentiometer. Please try again.');
          }
        }
        debounceTimer = null;
      }, 300); // Wait 300ms after user stops moving slider
    } else {
      // Immediate update (for non-slider controls like checkboxes)
      try {
        await updateState({
          potentiometers: {
            [potDef.id]: {
              ...potState,
              ...filteredUpdates
            }
          }
        });
      } catch (error) {
        console.error('Failed to update potentiometer:', error);
        alert('Failed to update potentiometer. Please try again.');
      }
    }
  }

  function toggleExpanded() {
    expanded = !expanded;
  }

  // ✅ Get voltage from state if available, otherwise calculate from wiper position
  // Voltage range depends on power setting: 0-5V or 0-12V
  const maxVoltage = $derived(powerVoltage === '12V' ? 12.0 : 5.0);
  const voltage = $derived(potState ? (potState.voltage ?? (potState.wiper_position / 255) * maxVoltage) : 0);
  const isEnabled = $derived(potState?.enabled ?? false);
  
  // Cleanup debounce timer on destroy
  onDestroy(() => {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
  });
</script>

<div class="bg-dark-card rounded-lg border border-dark-accent/20 overflow-hidden">
  <!-- Summary View -->
  <button
    class="w-full p-4 flex items-center justify-between hover:bg-dark-surface/50 transition-colors"
    onclick={toggleExpanded}
  >
    <div class="flex items-center gap-4">
      <div class="flex items-center gap-2">
        <!-- Status Indicator Circle -->
        <div
          class="w-4 h-4 rounded-full transition-colors"
          class:bg-green-500={isEnabled}
          class:bg-red-500={!isEnabled}
          title={isEnabled ? 'Potentiometer is ON' : 'Potentiometer is OFF'}
        ></div>
        <div class="bg-dark-accent text-dark-bg rounded px-3 py-1 font-bold">
          U{potDef.port}
        </div>
      </div>
      <div class="text-left">
        <div class="font-semibold">{potDef.name}</div>
        <div class="text-sm text-gray-400">{potDef.pin} • {potDef.resistance}</div>
      </div>
    </div>
    <div class="text-right">
      {#if potState}
        <div class="font-semibold">{voltage.toFixed(2)}V</div>
        <div class="text-sm text-gray-400">{potState.wiper_position}</div>
      {/if}
      <div class="text-xl mt-1">{expanded ? '▲' : '▼'}</div>
    </div>
  </button>

  <!-- Expanded View -->
  {#if expanded && potState}
    <div class="border-t border-dark-accent/20 p-6 space-y-4">
      <!-- Fixed Fields (Read-only) -->
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div>
          <div class="text-gray-400">Pin</div>
          <div class="font-semibold">{potDef.pin}</div>
        </div>
        <div>
          <div class="text-gray-400">Port</div>
          <div class="font-semibold">{potDef.port}</div>
        </div>
        <div>
          <div class="text-gray-400">Resistance</div>
          <div class="font-semibold">{potDef.resistance}</div>
        </div>
        <div>
          <div class="text-gray-400">Fault Range</div>
          <div class="font-semibold">{potDef.ecm_fault_low}-{potDef.ecm_fault_high}</div>
        </div>
      </div>

      <!-- Wiper Position Slider -->
      <div>
        <label for="wiper-position-{potDef.id}" class="block text-sm text-gray-400 mb-2">
          Wiper Position: {displayWiperPosition} ({((displayWiperPosition / 255) * maxVoltage).toFixed(2)}V)
        </label>
        <input
          id="wiper-position-{potDef.id}"
          type="range"
          min="0"
          max="255"
          value={displayWiperPosition}
          oninput={(e) => {
            const wiperPosition = parseInt(e.currentTarget.value);
            const calculatedVoltage = (wiperPosition / 255) * maxVoltage;
            // Update local state immediately for UI responsiveness
            localWiperPosition = wiperPosition;
            // Debounce the actual API call to avoid timeout errors from rapid updates
            updatePot({ wiper_position: wiperPosition, voltage: calculatedVoltage }, true);
          }}
          class="w-full h-2 bg-dark-surface rounded-lg appearance-none cursor-pointer accent-dark-accent"
          style="min-height: 44px;"
        />
        <div class="flex justify-between text-xs text-gray-400 mt-1">
          <span>0.0V</span>
          <span>{maxVoltage.toFixed(1)}V</span>
        </div>
      </div>

      <!-- On/Off Toggle -->
      <div>
        <div class="block text-sm text-gray-400 mb-2">Potentiometer State</div>
        <button
          class="w-full px-6 py-4 rounded font-semibold transition-colors min-h-touch"
          class:bg-green-600={isEnabled}
          class:hover:bg-green-700={isEnabled}
          class:bg-red-600={!isEnabled}
          class:hover:bg-red-700={!isEnabled}
          onclick={() => updatePot({ enabled: !isEnabled })}
        >
          {isEnabled ? 'On' : 'Off'}
        </button>
      </div>

      <!-- ECU Function (Read-only from selected ECU) -->
      <div>
        <div class="text-sm text-gray-400 mb-1">ECU Function Description</div>
        <div class="px-4 py-2 rounded bg-dark-surface border border-dark-accent/20 text-gray-300 min-h-touch">
          {ecuPinConfig?.ecu_function || 'Not configured'}
        </div>
      </div>

      <!-- Wire Color (Read-only from selected ECU) -->
      <div>
        <div class="text-sm text-gray-400 mb-1">Wire Color</div>
        <div class="px-4 py-2 rounded bg-dark-surface border border-dark-accent/20 text-gray-300 min-h-touch">
          {ecuPinConfig?.wire_color || 'Not specified'}
        </div>
      </div>
    </div>
  {/if}
</div>
