<script lang="ts">
  import { slide, fade } from 'svelte/transition';
  import { trainWorld } from '../stores/trainWorld.svelte';
  import { conductorState } from '../stores/conductorState.svelte';
  import { playClickSound, playSuccessSound, playCallBell } from '../utils/audio';

  let isOpen = $state(false);

  function toggleRadio() {
    isOpen = !isOpen;
    if (isOpen) playClickSound();
  }

  function handleReportPreTrip() {
    playSuccessSound();
    isOpen = false;
    trainWorld.showToast('Рация: ЛНП', 'Вас понял. Ремонтная бригада уже в пути. Продолжайте подготовку к рейсу.', 5000);
    trainWorld.setPreTripNeedsRadio(false);
    trainWorld.completePreTrip();
  }

  function handleGenericCall(target: string) {
    playCallBell();
    isOpen = false;
    trainWorld.showToast(`Рация: ${target}`, 'На связи. Опишите ситуацию (В разработке).');
  }
</script>

<div class="fixed bottom-24 right-4 z-50 flex flex-col items-end gap-3 pointer-events-auto">

  {#if isOpen}
    <div transition:slide={{duration: 200, axis: 'y'}} class="w-64 bg-[#1a1816] border-2 border-stone-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
      <!-- Антенна / Шапка рации -->
      <div class="bg-stone-900 p-3 border-b border-stone-800 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span class="text-xs font-mono font-bold text-stone-300">КАНАЛ 1 (ШТАБ)</span>
        </div>
        <button onclick={toggleRadio} class="text-stone-500 hover:text-white cursor-pointer">✕</button>
      </div>

      <div class="p-2 flex flex-col gap-1.5">
        {#if conductorState.shiftPhase === 'initial_round' && trainWorld.preTripNeedsRadio}
          <button
            onclick={handleReportPreTrip}
            class="w-full text-left px-3 py-2.5 bg-rose-950/40 hover:bg-rose-900/60 border border-rose-500/50 rounded-lg text-rose-300 text-xs font-bold transition-colors cursor-pointer animate-pulse"
          >
            ⚠️ Доложить ЛНП о поломках
          </button>
        {/if}

        <button onclick={() => handleGenericCall('Начальник поезда (ЛНП)')} class="w-full text-left px-3 py-2.5 bg-[#24201c] hover:bg-[#2d2924] border border-[#3d3831] rounded-lg text-stone-300 text-xs font-semibold transition-colors cursor-pointer">
          📞 Связь с ЛНП
        </button>
        <button onclick={() => handleGenericCall('Транспортная безопасность')} class="w-full text-left px-3 py-2.5 bg-[#24201c] hover:bg-[#2d2924] border border-[#3d3831] rounded-lg text-stone-300 text-xs font-semibold transition-colors cursor-pointer">
          👮 Вызвать ПТБ (Охрана)
        </button>
        <button onclick={() => handleGenericCall('Поездной электромеханик')} class="w-full text-left px-3 py-2.5 bg-[#24201c] hover:bg-[#2d2924] border border-[#3d3831] rounded-lg text-stone-300 text-xs font-semibold transition-colors cursor-pointer">
          🔧 Вызвать ПЭМ (Техник)
        </button>
      </div>
    </div>
  {/if}

  <!-- Кнопка рации -->
  <button
    onclick={toggleRadio}
    class="w-14 h-14 bg-stone-900 border-2 rounded-2xl flex items-center justify-center text-2xl shadow-[0_10px_25px_rgba(0,0,0,0.8)] transition-all hover:-translate-y-1 cursor-pointer {trainWorld.preTripNeedsRadio && !isOpen ? 'border-rose-500 shadow-[0_0_20px_rgba(225,29,72,0.5)] animate-pulse' : 'border-stone-700 hover:border-amber-500'}"
    title="Служебная рация"
  >
    📻
    {#if trainWorld.preTripNeedsRadio && !isOpen}
      <span class="absolute -top-1 -right-1 w-3.5 h-3.5 bg-rose-500 rounded-full border-2 border-stone-900"></span>
    {/if}
  </button>
</div>