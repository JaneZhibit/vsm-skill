<script lang="ts">
  import { fade, slide } from 'svelte/transition';
  import { trainWorld, type PassengerMood, type CabinView } from '../stores/trainWorld.svelte';
  import { ROUTE_CHECKPOINTS } from '../config/routeConfig';

  let isOpen = $state<boolean>(false);

  function toggleOpen() {
    isOpen = !isOpen;
  }


  function handleRealTime() {
    trainWorld.setRealTime();
  }

  function handleFastForwardNext() {
    trainWorld.fastForwardToNextCheckpoint();
  }

  function handleInterruptEmergency() {
    trainWorld.interrupt('Аварийное торможение / Прерывание по сигналу проводника');
  }

  function handleJump(index: number) {
    trainWorld.jumpTo(index);
  }

  function handleMood(mood: PassengerMood) {
    trainWorld.setPassengerMood(mood);
  }

  function handleSwitchView(view: CabinView) {
    trainWorld.switchView(view);
  }

  function handleResetScenario() {
    trainWorld.resetScenario();
  }
</script>

<!-- Плавающий виджет отладки в правом нижнем углу экрана -->
<div class="fixed bottom-3 right-3 z-50 flex flex-col items-end gap-2 pointer-events-auto">
  <!-- Всплывающая панель настроек / отладки -->
  {#if isOpen}
    <div
      transition:slide={{ duration: 200 }}
      class="w-96 max-w-[calc(100vw-24px)] bg-slate-900/95 border border-slate-700/90 rounded-2xl p-4 shadow-2xl backdrop-blur-xl flex flex-col gap-3 text-xs text-slate-200"
    >
      <!-- Шапка панели отладки -->
      <div class="flex items-center justify-between border-b border-slate-800 pb-2">
        <div class="flex items-center gap-2">
          <span class="text-sm">⚙️</span>
          <span class="font-bold tracking-wide uppercase text-white text-[11px]">
            Отладка симуляции ВСМ-1
          </span>
        </div>
        <button
          onclick={toggleOpen}
          class="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 cursor-pointer"
          title="Закрыть панель отладки"
        >
          ✕
        </button>
      </div>

      <!-- Метрики времени и скорости -->
      <div class="flex items-center justify-between bg-[#141210]/80 p-2.5 rounded-lg border border-[#2d2924]">
        <div>
          <span class="text-[10px] text-[#a39e95] uppercase font-mono block">Время:</span>
          <span class="font-mono font-bold text-amber-400 text-sm">{trainWorld.formattedTime}</span>
        </div>
        <div>
          <span class="text-[10px] text-[#a39e95] uppercase font-mono block">Скорость:</span>
          <span class="font-mono font-bold text-[#f5f3ef] text-sm">{Math.round(trainWorld.speed)} км/ч</span>
        </div>
        <div>
          <span class="text-[10px] text-[#a39e95] uppercase font-mono block">Режим:</span>
          <span class="font-mono text-[11px] {trainWorld.isFastForwarding ? 'text-amber-400 font-bold animate-pulse' : trainWorld.isPaused ? 'text-rose-400 font-bold' : 'text-emerald-400'}">
            {trainWorld.isFastForwarding ? '⏩ 90x' : trainWorld.isPaused ? '⏸ Пауза' : '1:1'}
          </span>
        </div>
      </div>

      <!-- Кнопки управления временем -->
      <div class="flex flex-wrap items-center gap-1.5">
        <button
          onclick={handleRealTime}
          class="flex-1 py-1.5 px-2 rounded-lg font-semibold bg-[#282420] hover:bg-[#342f2a] text-slate-200 border border-[#3d3831] cursor-pointer text-center"
        >
          1:1 Время
        </button>
        <button
          onclick={handleFastForwardNext}
          disabled={trainWorld.isFastForwarding || !trainWorld.nextCheckpoint}
          class="flex-1 py-1.5 px-2 rounded-lg font-bold bg-amber-600 hover:bg-amber-500 text-stone-950 border border-amber-500 cursor-pointer disabled:opacity-40 text-center"
        >
          ⏩ След. точка
        </button>
        <button
          onclick={handleInterruptEmergency}
          class="py-1.5 px-2.5 rounded-lg font-bold bg-rose-600 hover:bg-rose-500 text-white border border-rose-500 cursor-pointer text-center"
          title="Имитация ЧП"
        >
          🚨 ЧП
        </button>
      </div>

      <!-- Управление геймплеем и сценарием -->
      <div class="pt-2 border-t border-[#2d2924] flex flex-col gap-2">
        <div class="text-[10px] text-[#a39e95] uppercase font-semibold">Сценарий и вызов проводника:</div>
        <div class="flex items-center gap-2">
          <button
            onclick={() => handleSwitchView('aisle')}
            class="flex-1 py-1 rounded bg-[#282420] hover:bg-[#342f2a] border border-[#3d3831] text-[11px] {trainWorld.currentView === 'aisle' ? 'border-amber-400 text-amber-300 font-bold' : 'text-[#a39e95]'} cursor-pointer"
          >
            🚶 Проход
          </button>
          <button
            onclick={() => handleSwitchView('seat')}
            class="flex-1 py-1 rounded bg-[#282420] hover:bg-[#342f2a] border border-[#3d3831] text-[11px] {trainWorld.currentView === 'seat' ? 'border-amber-400 text-amber-300 font-bold' : 'text-[#a39e95]'} cursor-pointer"
          >
            💺 Место 2А
          </button>
          <button
            onclick={handleResetScenario}
            class="py-1 px-2.5 rounded bg-amber-600 hover:bg-amber-500 text-black font-bold text-[11px] cursor-pointer"
          >
            🛎️ Вызов
          </button>
        </div>

        <!-- Настроение пассажира -->
        <div class="flex items-center gap-1.5 pt-1">
          <span class="text-[10px] text-slate-400">Эмоция:</span>
          <button
            onclick={() => handleMood('calm')}
            class="flex-1 py-0.5 rounded text-[10px] border {trainWorld.passengerMood === 'calm' ? 'bg-emerald-600 border-emerald-400 text-white font-bold' : 'bg-slate-800 border-slate-700 text-slate-300'} cursor-pointer"
          >
            Спокоен
          </button>
          <button
            onclick={() => handleMood('annoyed')}
            class="flex-1 py-0.5 rounded text-[10px] border {trainWorld.passengerMood === 'annoyed' ? 'bg-rose-600 border-rose-400 text-white font-bold' : 'bg-slate-800 border-slate-700 text-slate-300'} cursor-pointer"
          >
            Претензия
          </button>
          <button
            onclick={() => handleMood('empty')}
            class="flex-1 py-0.5 rounded text-[10px] border {trainWorld.passengerMood === 'empty' ? 'bg-slate-700 border-slate-500 text-white font-bold' : 'bg-slate-800 border-slate-700 text-slate-300'} cursor-pointer"
          >
            Пусто
          </button>
        </div>
      </div>

      <!-- Быстрый телепорт по маршруту -->
      <div class="pt-2 border-t border-slate-800 flex flex-col gap-1.5">
        <span class="text-[10px] text-slate-400 uppercase font-semibold">Чекпоинты ВСМ-1:</span>
        <div class="grid grid-cols-3 gap-1">
          {#each ROUTE_CHECKPOINTS as cp, idx}
            <button
              onclick={() => handleJump(idx)}
              class="py-1 px-1.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300 hover:text-amber-300 border border-slate-700 text-center truncate cursor-pointer"
              title={`${cp.plannedTime} — ${cp.label} (${cp.baseSpeed} км/ч)`}
            >
              {cp.label.split(' ')[0]}
            </button>
          {/each}
        </div>
      </div>
    </div>
  {/if}

  <!-- Компактная плавающая кнопка открытия/закрытия виджета -->
  <button
    onclick={toggleOpen}
    class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-900/90 hover:bg-slate-800 active:bg-slate-950 border border-slate-700/80 text-slate-300 hover:text-white shadow-xl backdrop-blur-md text-xs font-semibold cursor-pointer transition-all hover:scale-105"
  >
    <span class="text-xs">⚙️</span>
    <span>Отладка / Чекпоинты</span>
    <span class="text-[10px] text-slate-500">{isOpen ? '▲' : '▼'}</span>
  </button>
</div>
