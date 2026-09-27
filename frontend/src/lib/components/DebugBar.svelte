<script lang="ts">
  import { fade, slide } from 'svelte/transition';
  import { trainWorld } from '../stores/trainWorld.svelte';
  import { physicsState } from '../stores/trainPhysics.svelte';
  import { cabinState, type PassengerMood, type CabinView } from '../stores/cabinState.svelte';
  import { conductorState } from '../stores/conductorState.svelte';
  import { ROUTE_CHECKPOINTS } from '../config/routeConfig';

  let isOpen = $state<boolean>(false);

  function toggleOpen() { isOpen = !isOpen; }

  function handleRealTime() { physicsState.setRealTime(); }

  function handleFastForwardNext() {
    const next = physicsState.nextCheckpoint;
    if (next) trainWorld.fastForwardTo(next.checkpoint.plannedTime);
  }

  function handleInterruptEmergency() {
    physicsState.setRealTime();
    conductorState.triggerEmergency('Аварийное торможение / Прерывание по сигналу проводника');
  }

  function handleJump(index: number) { trainWorld.jumpTo(index); }
  function handleMood(mood: PassengerMood) { cabinState.setPassengerMood(mood); }
  function handleSwitchView(view: CabinView) { cabinState.switchView(view); }
  function handleResetScenario() { cabinState.resetScenario(); }
</script>

<div class="fixed bottom-3 right-3 z-50 flex flex-col items-end gap-2 pointer-events-auto">
  {#if isOpen}
    <div transition:slide={{ duration: 200 }} class="w-96 max-w-[calc(100vw-24px)] bg-slate-900/95 border border-slate-700/90 rounded-2xl p-4 shadow-2xl backdrop-blur-xl flex flex-col gap-3 text-xs text-slate-200">

      <div class="flex items-center justify-between border-b border-slate-800 pb-2">
        <div class="flex items-center gap-2"><span class="text-sm">⚙️</span><span class="font-bold tracking-wide uppercase text-white text-[11px]">Отладка симуляции ВСМ-1</span></div>
        <button onclick={toggleOpen} class="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 cursor-pointer">✕</button>
      </div>

      <div class="flex items-center justify-between bg-[#141210]/80 p-2.5 rounded-lg border border-[#2d2924]">
        <div>
          <span class="text-[10px] text-[#a39e95] uppercase font-mono block">Время:</span>
          <span class="font-mono font-bold text-amber-400 text-sm">{physicsState.formattedTime}</span>
        </div>
        <div>
          <span class="text-[10px] text-[#a39e95] uppercase font-mono block">Скорость:</span>
          <span class="font-mono font-bold text-[#f5f3ef] text-sm">{Math.round(physicsState.speed)} км/ч</span>
        </div>
        <div>
          <span class="text-[10px] text-[#a39e95] uppercase font-mono block">Режим:</span>
          <span class="font-mono text-[11px] {physicsState.isFastForwarding ? 'text-amber-400 font-bold animate-pulse' : physicsState.isPaused ? 'text-rose-400 font-bold' : 'text-emerald-400'}">
            {physicsState.isFastForwarding ? '⏩ 90x' : physicsState.isPaused ? '⏸ Пауза' : '1:1'}
          </span>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-1.5">
        <button onclick={handleRealTime} class="flex-1 py-1.5 px-2 rounded-lg font-semibold bg-[#282420] hover:bg-[#342f2a] text-slate-200 border border-[#3d3831] cursor-pointer text-center">1:1 Время</button>
        <button onclick={handleFastForwardNext} disabled={physicsState.isFastForwarding || !physicsState.nextCheckpoint} class="flex-1 py-1.5 px-2 rounded-lg font-bold bg-amber-600 hover:bg-amber-500 text-stone-950 border border-amber-500 cursor-pointer disabled:opacity-40 text-center">⏩ След. точка</button>
        <button onclick={handleInterruptEmergency} class="py-1.5 px-2.5 rounded-lg font-bold bg-rose-600 hover:bg-rose-500 text-white border border-rose-500 cursor-pointer text-center">🚨 ЧП</button>
      </div>

      <div class="pt-2 border-t border-[#2d2924] flex flex-col gap-2">
        <div class="text-[10px] text-[#a39e95] uppercase font-semibold">Сценарий и вызов:</div>
        <div class="flex items-center gap-2">
          <button onclick={() => handleSwitchView('aisle')} class="flex-1 py-1 rounded bg-[#282420] hover:bg-[#342f2a] border border-[#3d3831] text-[11px] {cabinState.currentView === 'aisle' ? 'border-amber-400 text-amber-300 font-bold' : 'text-[#a39e95]'} cursor-pointer">🚶 Проход</button>
          <button onclick={() => handleSwitchView('seat')} class="flex-1 py-1 rounded bg-[#282420] hover:bg-[#342f2a] border border-[#3d3831] text-[11px] {cabinState.currentView === 'seat' ? 'border-amber-400 text-amber-300 font-bold' : 'text-[#a39e95]'} cursor-pointer">💺 Место 2А</button>
          <button onclick={handleResetScenario} class="py-1 px-2.5 rounded bg-amber-600 hover:bg-amber-500 text-black font-bold text-[11px] cursor-pointer">🛎️ Вызов</button>
        </div>

        <div class="flex items-center gap-1.5 pt-1">
          <span class="text-[10px] text-slate-400">Эмоция:</span>
          <button onclick={() => handleMood('calm')} class="flex-1 py-0.5 rounded text-[10px] border {cabinState.passengerMood === 'calm' ? 'bg-emerald-600 border-emerald-400 text-white font-bold' : 'bg-slate-800 border-slate-700 text-slate-300'} cursor-pointer">Спокоен</button>
          <button onclick={() => handleMood('annoyed')} class="flex-1 py-0.5 rounded text-[10px] border {cabinState.passengerMood === 'annoyed' ? 'bg-rose-600 border-rose-400 text-white font-bold' : 'bg-slate-800 border-slate-700 text-slate-300'} cursor-pointer">Претензия</button>
          <button onclick={() => handleMood('empty')} class="flex-1 py-0.5 rounded text-[10px] border {cabinState.passengerMood === 'empty' ? 'bg-slate-700 border-slate-500 text-white font-bold' : 'bg-slate-800 border-slate-700 text-slate-300'} cursor-pointer">Пусто</button>
        </div>
      </div>

      <div class="pt-2 border-t border-slate-800 flex flex-col gap-1.5">
        <span class="text-[10px] text-slate-400 uppercase font-semibold">Чекпоинты ВСМ-1:</span>
        <div class="grid grid-cols-3 gap-1">
          {#each ROUTE_CHECKPOINTS as cp, idx}
            <button onclick={() => handleJump(idx)} class="py-1 px-1.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300 hover:text-amber-300 border border-slate-700 text-center truncate cursor-pointer">{cp.label.split(' ')[0]}</button>
          {/each}
        </div>
      </div>
    </div>
  {/if}

  <button onclick={toggleOpen} class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-900/90 hover:bg-slate-800 active:bg-slate-950 border border-slate-700/80 text-slate-300 hover:text-white shadow-xl backdrop-blur-md text-xs font-semibold cursor-pointer transition-all hover:scale-105">
    <span class="text-xs">⚙️</span><span>Отладка / Чекпоинты</span><span class="text-[10px] text-slate-500">{isOpen ? '▲' : '▼'}</span>
  </button>
</div>