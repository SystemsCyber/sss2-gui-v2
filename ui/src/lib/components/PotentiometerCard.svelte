<script lang="ts">
  import type { PotentiometerDefinition, PotentiometerState } from '$lib/api/client';
  import { deviceStore, updateState } from '$lib/stores/deviceStore.svelte';

  // ✅ Using $props() rune for component props (Svelte 5)
  let { potDef }: { potDef: PotentiometerDefinition } = $props();
  
  let expanded = $state(false);
  
  // ✅ Using $derived rune for reactive state
  const potState = $derived(deviceStore.deviceState?.potentiometers?.[potDef.id] as PotentiometerState | undefined);

  async function updatePot(updates: Partial<PotentiometerState>) {
    if (!potState) return;
    
    try {
      await updateState({
        potentiometers: {
          [potDef.id]: {
            ...potState,
            ...updates
          }
        }
      });
    } catch (error) {
      console.error('Failed to update potentiometer:', error);
      alert('Failed to update potentiometer. Please try again.');
    }
  }

  function toggleExpanded() {
    expanded = !expanded;
  }

  // ✅ Calculate voltage from wiper position (0-255 maps to 0.0V-5.0V) using $derived
  const voltage = $derived(potState ? (potState.wiper_position / 255) * 5.0 : 0);
</script>

<div class="bg-dark-card rounded-lg border border-dark-accent/20 overflow-hidden">
  <!-- Summary View -->
  <button
    class="w-full p-4 flex items-center justify-between hover:bg-dark-surface/50 transition-colors"
    onclick={toggleExpanded}
  >
    <div class="flex items-center gap-4">
      <div class="bg-dark-accent text-dark-bg rounded px-3 py-1 font-bold">
        U{potDef.port}
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
          Wiper Position: {potState.wiper_position} ({voltage.toFixed(2)}V)
        </label>
        <input
          id="wiper-position-{potDef.id}"
          type="range"
          min="0"
          max="255"
          value={potState.wiper_position}
          oninput={(e) => updatePot({ wiper_position: parseInt(e.currentTarget.value) })}
          class="w-full h-2 bg-dark-surface rounded-lg appearance-none cursor-pointer accent-dark-accent"
          style="min-height: 44px;"
        />
        <div class="flex justify-between text-xs text-gray-400 mt-1">
          <span>0.0V</span>
          <span>5.0V</span>
        </div>
      </div>

      <!-- Terminal Connections -->
      <div>
        <div class="block text-sm text-gray-400 mb-2">Terminals</div>
        <div class="flex gap-6">
          <label class="flex items-center gap-2 cursor-pointer min-h-touch">
            <input
              type="checkbox"
              checked={potState.term_a_connect}
              onchange={(e) => updatePot({ term_a_connect: e.currentTarget.checked })}
              class="w-6 h-6 accent-dark-accent"
            />
            <span>Term A</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer min-h-touch">
            <input
              type="checkbox"
              checked={potState.wiper_connect}
              onchange={(e) => updatePot({ wiper_connect: e.currentTarget.checked })}
              class="w-6 h-6 accent-dark-accent"
            />
            <span>Wiper</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer min-h-touch">
            <input
              type="checkbox"
              checked={potState.term_b_connect}
              onchange={(e) => updatePot({ term_b_connect: e.currentTarget.checked })}
              class="w-6 h-6 accent-dark-accent"
            />
            <span>Term B</span>
          </label>
        </div>
      </div>

      <!-- Application -->
      <div>
        <label for="application-{potDef.id}" class="block text-sm text-gray-400 mb-2">ECU Application Description</label>
        <input
          id="application-{potDef.id}"
          type="text"
          value={potState.application}
          oninput={(e) => updatePot({ application: e.currentTarget.value })}
          placeholder="Application description"
          class="w-full px-4 py-2 rounded bg-dark-surface border border-dark-accent/20 focus:border-dark-accent focus:outline-none min-h-touch"
        />
      </div>

      <!-- Wire Color -->
      <div>
        <label for="wire-color-{potDef.id}" class="block text-sm text-gray-400 mb-2">Wire Color</label>
        <input
          id="wire-color-{potDef.id}"
          type="text"
          value={potState.wire_color}
          oninput={(e) => updatePot({ wire_color: e.currentTarget.value })}
          placeholder="e.g. PPL/WHT"
          class="w-full px-4 py-2 rounded bg-dark-surface border border-dark-accent/20 focus:border-dark-accent focus:outline-none min-h-touch"
        />
      </div>
    </div>
  {/if}
</div>
