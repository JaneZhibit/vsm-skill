<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fade, fly } from 'svelte/transition';

  // Утилиты и сторы
  import { trainWorld } from '../../stores/trainWorld.svelte';
  import { cabinState } from '../../stores/cabinState.svelte';
  import { physicsState } from '../../stores/trainPhysics.svelte';
  import { conductorState } from '../../stores/conductorState.svelte';
  import { trainAudio } from '../../stores/trainAudio.svelte';
  import { authStore } from '../../stores/authStore.svelte';
  import { playCallBell, playClickSound, playSuccessSound } from '../../utils/audio';

  // Компоненты
  import CeilingDisplay from '../CeilingDisplay.svelte';
  import ConductorDialogue from '../ConductorDialogue.svelte';
  import SeatMapModal from '../SeatMapModal.svelte';
  import ShiftDebriefModal from '../ShiftDebriefModal.svelte';
  import RadioTool from '../RadioTool.svelte';
  import CleaningMiniGame from './CleaningMiniGame.svelte';
  import PreTripMiniGame from './PreTripMiniGame.svelte';

  let isSeatMapOpen = $state<boolean>(false);
  let isDebriefOpen = $state<boolean>(false);
  let isSettingsOpen = $state<boolean>(false);
  let isInfoCollapsed = $state<boolean>(false);

  let selectedSeat = $derived(cabinState.selectedSeat);
  let callingSeat = $derived(
    cabinState.seats.find(
      (s) =>
        s.activeIncident != null &&
        (typeof s.activeIncident === 'string' || s.activeIncident.phase !== 'passive')
    )
  );

  const isTripFinished = $derived(physicsState.currentKm >= 678.5 || physicsState.timeSeconds >= 58500);

  const isCabinEmpty = $derived(
    conductorState.shiftPhase === 'initial_round' ||
    conductorState.shiftPhase === 'arrival' ||
    isTripFinished ||
    cabinState.occupiedSeatsCount === 0
  );

  const cabinImageSrc = $derived(isCabinEmpty ? '/assets/cabin.jpg' : '/assets/cabin_aisle_transparent.png');

  // --- БЛОКИРОВКА КНОПКИ "НАЗАД" НА ANDROID ---
  onMount(() => {
    window.history.pushState({ simulatorLocked: true }, '', window.location.href);

    const handlePopState = (e: PopStateEvent) => {
      window.history.pushState({ simulatorLocked: true }, '', window.location.href);
      if (!isSettingsOpen && !isSeatMapOpen) {
        playClickSound();
        isSettingsOpen = true;
      } else if (isSeatMapOpen) {
        isSeatMapOpen = false;
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  });
  // -------------------------------------------

  function getSeatCoords(seatId: string) {
    const row = parseInt(seatId.slice(0, -1)) || 2;
    const letter = seatId.slice(-1);
    const isLeft = letter === 'A' || letter === 'B';
    const depth = Math.min(1, Math.max(0, (row - 1) / 11));
    const top = 62 - depth * 28;
    const left = isLeft ? 18 + depth * 25 : 82 - depth * 25;
    const scale = 1.05 - depth * 0.4;
    return { top: `${top}%`, left: `${left}%`, scale, isLeft };
  }

  function handleCallClick(seatId?: string) {
    playCallBell();
    if (seatId) cabinState.inspectSeat(seatId);
    else {
      const activeSeat = cabinState.seats.find((s) => s.activeIncident != null);
      if (activeSeat) cabinState.inspectSeat(activeSeat.id);
    }
  }

  function handlePrevSeat() { playClickSound(); cabinState.prevOccupiedSeat(); if (cabinState.selectedSeat) cabinState.inspectSeat(cabinState.selectedSeat.id); }
  function handleNextSeat() { playClickSound(); cabinState.nextOccupiedSeat(); if (cabinState.selectedSeat) cabinState.inspectSeat(cabinState.selectedSeat.id); }
  function handleOpenSeatMap() { playClickSound(); isSeatMapOpen = true; }

  function handleExitToMenu() {
    playClickSound();
    trainWorld.abortTrip();
    authStore.setRoute('trips');
  }

  let scrollAreaEl = $state<HTMLElement | null>(null);

  function centerScroll(smooth = true) {
    if (!scrollAreaEl) return;
    const maxScroll = scrollAreaEl.scrollWidth - scrollAreaEl.clientWidth;
    if (maxScroll <= 0) return;
    let targetLeft = maxScroll / 2;
    if (cabinState.currentView === 'seat') {
      const letter = selectedSeat?.id.slice(-1);
      if (letter === 'A' || letter === 'B') targetLeft = maxScroll * 0.22;
      else if (letter === 'C' || letter === 'D') targetLeft = maxScroll * 0.78;
    } else if (cabinState.currentView === 'aisle' && callingSeat) {
      const letter = callingSeat.id.slice(-1);
      if (letter === 'A' || letter === 'B') targetLeft = maxScroll * 0.25;
      else if (letter === 'C' || letter === 'D') targetLeft = maxScroll * 0.75;
    }
    scrollAreaEl.scrollTo({ left: targetLeft, behavior: smooth ? 'smooth' : 'auto' });
  }

  $effect(() => {
    const view = cabinState.currentView;
    const seatId = selectedSeat?.id;
    const callId = callingSeat?.id;
    const timer = setTimeout(() => centerScroll(true), 120);
    return () => clearTimeout(timer);
  });

  function handleWindowResize() { centerScroll(false); }

  function panLeft() { if(scrollAreaEl) scrollAreaEl.scrollBy({left: -250, behavior: 'smooth'}); }
  function panRight() { if(scrollAreaEl) scrollAreaEl.scrollBy({left: 250, behavior: 'smooth'}); }
</script>

<svelte:window onresize={handleWindowResize} />

<div class="cabin-viewport">
  <RadioTool />

  {#if trainWorld.stationToast}
    <div class="station-toast-overlay" transition:fly={{ y: -20, duration: 250 }}>
      <div class="toast-card">
        <div class="toast-title">{trainWorld.stationToast.title}</div>
        <div class="toast-subtitle">{trainWorld.stationToast.subtitle}</div>
      </div>
    </div>
  {/if}

  <!-- ВЕРХНИЙ HUD -->
  <div class="hud-top-bar">
    {#if cabinState.currentView === 'aisle'}
      <div class="aisle-phase-banner">
        {#if conductorState.shiftPhase === 'initial_round'}
          <div class="phase-banner-content phase-round">
            <span class="phase-text">📋 <strong>Приемка (13:50)</strong></span>
          </div>
        {:else if conductorState.shiftPhase === 'cruise'}
          <div class="phase-banner-content phase-cruise">
            <span class="phase-pulse-dot"></span>
            <span class="phase-text">⚡ <strong>{Math.round(physicsState.speed)} км/ч</strong></span>
          </div>
        {:else if conductorState.shiftPhase === 'station_warning' || conductorState.shiftPhase === 'tver_warning'}
          {@const exiting = cabinState.getNextStationExitingPassengers(physicsState.nextStation?.label || '')}
          <div class="phase-banner-content phase-warning">
            <span class="phase-text">⚠️ <strong>Прибытие (10м)</strong> • Выход: {exiting.length} чел.</span>
          </div>
        {:else}
          <div class="phase-banner-content phase-arrival">
            <span class="phase-text">🏁 <strong>Стоянка</strong></span>
          </div>
        {/if}
      </div>

      <div class="top-actions-cluster">
        <button onclick={handleOpenSeatMap} class="seat-map-trigger-btn" title="Схема вагона">
          <span class="trigger-icon">📋</span>
          <span class="trigger-text hidden sm:inline">Схема ({cabinState.occupiedSeatsCount}/48)</span>
          {#if cabinState.alertSeatsCount > 0}
            <span class="trigger-alert-badge"><span class="trigger-alert-ping"></span>{cabinState.alertSeatsCount}</span>
          {/if}
        </button>
        <button onclick={() => { playClickSound(); isSettingsOpen = true; }} class="seat-map-trigger-btn !px-3" title="Меню">
          <span class="trigger-icon text-base">⚙️</span>
        </button>
      </div>
    {:else}
      <div class="seat-top-bar">
        <!-- Оставим только кнопки здесь, т.к. "В проход" теперь внутри диалога -->
      </div>
    {/if}
  </div>

  <!-- КНОПКИ ПАНОРАМИРОВАНИЯ ДЛЯ МОБИЛЬНЫХ УСТРОЙСТВ -->
  {#if cabinState.currentView === 'aisle'}
    <button onclick={panLeft} class="md:hidden pan-arrow left-arrow" aria-label="Влево">❮</button>
    <button onclick={panRight} class="md:hidden pan-arrow right-arrow" aria-label="Вправо">❯</button>
  {/if}

  <div class="scene-scroll-area hide-scrollbar" bind:this={scrollAreaEl}>
    {#if cabinState.currentView === 'aisle'}
      <div class="scene-container aisle-scene" class:high-speed-shake={physicsState.speed > 250 && !physicsState.isPaused} class:ambient-sway={physicsState.speed > 5 && !physicsState.isPaused}>
        <div class="window-viewport left-viewport"><div class="parallax-layer sky-layer" class:is-moving={physicsState.speed > 5 && !physicsState.isPaused}></div><div class="parallax-layer ground-layer" class:is-moving={physicsState.speed > 5 && !physicsState.isPaused}></div></div>
        <div class="window-viewport right-viewport"><div class="parallax-layer sky-layer" class:is-moving={physicsState.speed > 5 && !physicsState.isPaused}></div><div class="parallax-layer ground-layer" class:is-moving={physicsState.speed > 5 && !physicsState.isPaused}></div></div>
        <div class="station-platform-layer" class:platform-visible={physicsState.speed < 5 && physicsState.movementStatus.includes('Стоянка')}></div>

        <img src={cabinImageSrc} alt="Вагон" class="base-image cabin-overlay" />
        <CeilingDisplay />

        {#if conductorState.shiftPhase === 'initial_round' && !trainWorld.isPreTripDone && !trainWorld.preTripNeedsRadio}
          <PreTripMiniGame />
        {/if}
        <CleaningMiniGame {isTripFinished} />

        {#if callingSeat}
          {@const pos = getSeatCoords(callingSeat.id)}
          <div class="absolute pointer-events-none z-20 w-32 h-32 rounded-full -translate-x-1/2 -translate-y-1/2 bg-rose-600/30 blur-2xl animate-pulse" style="top: {pos.top}; left: {pos.left};"></div>
          <button onclick={() => handleCallClick(callingSeat?.id)} class="aisle-call-badge" style="top: {pos.top}; left: {pos.left}; transform: translate(-50%, -50%) scale({pos.scale});">
            <span class="call-ping"></span>🛎️ Место {callingSeat.id} • {Math.ceil(trainWorld.reactionTimeLeft)} с ➔
          </button>
        {/if}

        {#each cabinState.seats.filter(s => s.isOccupied && ((s.activeIncident && typeof s.activeIncident === 'object' && s.activeIncident.phase === 'passive') || s.condition === 'drunk' || s.condition === 'sleeping')) as passiveSeat}
          {#if !callingSeat || callingSeat.id !== passiveSeat.id}
            {@const ppos = getSeatCoords(passiveSeat.id)}
            <button onclick={() => handleCallClick(passiveSeat.id)} class="aisle-call-badge !bg-stone-900/90 !border-amber-500/60 hover:!bg-stone-800 text-amber-200" style="top: {ppos.top}; left: {ppos.left}; transform: translate(-50%, -50%) scale({ppos.scale * 0.85});">
              <span>{#if passiveSeat.activeIncident && typeof passiveSeat.activeIncident === 'object' && passiveSeat.activeIncident.phase === 'passive'}👁️ {passiveSeat.id}{:else if passiveSeat.condition === 'drunk'}🍺 {passiveSeat.id}{:else}💤 {passiveSeat.id}{/if}</span>
            </button>
          {/if}
        {/each}
      </div>
    {:else}
      <div class="scene-container seat-scene" class:ambient-sway={physicsState.speed > 5 && !physicsState.isPaused}>
        <img src="/assets/seat_bg.png" alt="Салон" class="base-image" />
        {#if selectedSeat?.isOccupied && selectedSeat?.passenger}
          {@const p = selectedSeat.passenger}
          {@const cleanSprite = (cabinState.currentPassengerSprite || p.sprite_url || '').replace('/assets/passengers/', '/assets/')}
          <img src={cleanSprite} alt={p.full_name} class="passenger-overlay" onerror={(e) => { const target = e.currentTarget as HTMLImageElement; target.src = `/assets/${p.archetype_id}/neutral.png`; }} />
        {:else if !isCabinEmpty && cabinState.passengerMood !== 'empty'}
          <img src={cabinState.passengerMood === 'calm' ? '/assets/passenger_calm.png' : '/assets/passenger_annoyed.png'} alt="Пассажир" class="passenger-overlay" />
        {/if}
      </div>
    {/if}
  </div>

  <!-- НИЖНЯЯ ПАНЕЛЬ С ДЕЙСТВИЯМИ И ИНФО -->
  {#if cabinState.currentView === 'aisle'}
    {@const isPreTripGameActive = conductorState.shiftPhase === 'initial_round' && !trainWorld.isPreTripDone && !trainWorld.preTripNeedsRadio}

    {#if !isPreTripGameActive}
      <div class="bottom-ui-panel pb-[max(0.5rem,env(safe-area-inset-bottom))]">
        <div class="pointer-events-auto w-full flex justify-center z-[50] relative px-3 md:px-0">
          {#if isTripFinished}
            <button onclick={() => { isDebriefOpen = true; }} disabled={!trainWorld.isPostTripDone} class="main-action-btn from-emerald-600 to-teal-500 border-emerald-400 {trainWorld.isPostTripDone ? 'animate-bounce' : 'grayscale opacity-80'}">
              <span>{trainWorld.isPostTripDone ? '🏁 Итоги смены ➔' : '🧹 Осмотр вагона...'}</span>
            </button>
          {:else if cabinState.alertSeatsCount > 0}
            {@const incSeat = cabinState.seats.find((s) => s.activeIncident != null)}
            <button onclick={() => handleCallClick(incSeat?.id)} class="main-action-btn from-rose-600 to-amber-500 border-rose-400 animate-pulse">
              <span>🚨 Место {incSeat?.id}: Решить ➔</span>
            </button>
          {:else if conductorState.shiftPhase === 'initial_round'}
            {#if trainWorld.preTripNeedsRadio}
              <button disabled class="main-action-btn bg-rose-900 opacity-90 border-rose-500 cursor-not-allowed">
                <span>📻 Доложите по рации...</span>
              </button>
            {:else}
              <button onclick={() => { playSuccessSound(); trainWorld.startCruisePhase(); }} disabled={!trainWorld.isPreTripDone} class="main-action-btn from-amber-600 to-yellow-500 text-stone-950 border-amber-400 {trainWorld.isPreTripDone ? '' : 'grayscale opacity-80'}">
                <span>{trainWorld.isPreTripDone ? '🚪 Начать посадку ➔' : '🔍 Приемка вагона...'}</span>
              </button>
            {/if}
          {:else if conductorState.shiftPhase === 'cruise'}
            <button onclick={() => { playClickSound(); trainWorld.skipToNextEvent(); }} class="main-action-btn from-cyan-600 to-teal-500 border-cyan-400">
              <span>⏩ Промотать событие ➔</span>
            </button>
          {:else if conductorState.shiftPhase === 'station_warning' || conductorState.shiftPhase === 'tver_warning'}
            <button onclick={() => { playClickSound(); trainWorld.skipToNextEvent(); }} class="main-action-btn from-rose-600 to-orange-500 border-rose-400">
              <span>🚉 К прибытию ➔</span>
            </button>
          {:else if conductorState.shiftPhase === 'arrival'}
            <button onclick={() => { playSuccessSound(); trainWorld.startCruisePhase(); }} class="main-action-btn from-amber-600 to-yellow-500 text-stone-950 border-amber-400">
              <span>⏩ Отправление дальше ➔</span>
            </button>
          {/if}
        </div>

        {#if !isTripFinished && conductorState.shiftPhase !== 'arrival'}
          <div class="pointer-events-auto w-full max-w-sm mx-auto flex flex-col items-center mt-1 px-3 md:px-0">
            <button onclick={() => {playClickSound(); isInfoCollapsed = !isInfoCollapsed;}} class="bg-[#141210]/95 border border-b-0 border-[#3d3831] rounded-t-xl px-6 py-1.5 flex items-center justify-center cursor-pointer shadow-md hover:bg-[#1a1816] transition-colors relative z-20">
              <span class="text-[10px] text-stone-400 font-bold uppercase tracking-widest">{isInfoCollapsed ? '▲ Маршрут' : '▼ Скрыть'}</span>
            </button>

            <!-- Плавное сворачивание через CSS max-height -->
            <div class="w-full bg-[#141210]/95 backdrop-blur-md border border-[#3d3831] rounded-xl rounded-t-none shadow-2xl flex flex-col relative z-10 transition-all duration-300 ease-in-out overflow-hidden {isInfoCollapsed ? 'max-h-0 opacity-0 border-none' : 'max-h-[100px] opacity-100 p-2.5 sm:p-3 border-t-0'}">
              <div class="flex justify-between items-center text-[10px] font-mono text-[#a39e95] uppercase font-semibold">
                <span class="text-amber-400 bg-[#282420] px-1.5 py-0.5 rounded border border-[#3d3831]">🕒 {physicsState.formattedTime}</span>
                <div class="text-center flex flex-col items-center leading-tight">
                  <span class="text-white truncate max-w-[120px]">След: {physicsState.nextStation?.label || 'С-Петербург'}</span>
                  <span class="opacity-60 text-[9px]">{physicsState.nextStation?.plannedTime || '16:15'}</span>
                </div>
              </div>
              <div class="relative w-full h-1.5 bg-[#2d2924] rounded-full mt-2">
                <div class="absolute top-0 left-0 h-full bg-amber-500 rounded-full transition-all duration-1000 ease-out" style="width: {physicsState.progressPercent}%"></div>
                <div class="absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 bg-white border border-amber-500 rounded-full shadow-[0_0_8px_rgba(245,158,11,0.8)] transition-all duration-1000 ease-out" style="left: {physicsState.progressPercent}%"></div>
              </div>
            </div>
          </div>
        {/if}
      </div>
    {/if}
  {:else}
    <div class="dialogue-wrapper">
      <ConductorDialogue />
    </div>
  {/if}

  <!-- МЕНЮ ПАУЗЫ -->
  {#if isSettingsOpen}
    <div class="fixed inset-0 z-[150] bg-black/85 backdrop-blur-sm flex items-center justify-center p-4" transition:fade={{duration: 150}}>
      <div class="w-full max-w-sm bg-[#1a1816] border border-[#3d3831] rounded-2xl p-5 shadow-2xl flex flex-col gap-4" transition:fly={{y: 20, duration: 200}}>
        <div class="text-center pb-3 border-b border-[#2d2924]">
          <h2 class="text-lg font-bold text-white mb-1">Меню симуляции</h2>
          <div class="text-xs font-mono text-amber-400">Рейс № 754 • {conductorState.conductorProfile.role}</div>
        </div>

        <div class="flex justify-between items-center bg-[#141210] p-3 rounded-xl border border-[#2d2924]">
          <span class="text-xs text-stone-400 uppercase font-bold">Оценка ЗУН:</span>
          <div class="flex gap-3 text-xs font-mono font-bold">
            <span class="text-amber-400">🤝 {conductorState.loyaltyScore}</span>
            <span class="text-emerald-400">🛡️ {conductorState.safetyScore}</span>
          </div>
        </div>

        <div class="flex flex-col gap-2.5">
          <button onclick={() => { playClickSound(); trainAudio.toggleAudio(); }} class="w-full p-3 rounded-xl bg-[#282420] hover:bg-[#342f2a] border border-[#3d3831] text-sm font-bold text-white transition-colors cursor-pointer flex justify-between items-center">
            <span>Звуки поезда</span>
            <span>{trainAudio.isAudioMuted ? '🔇 Выкл' : '🔊 Вкл'}</span>
          </button>

          <button onclick={handleExitToMenu} class="w-full p-3 rounded-xl bg-rose-950/40 hover:bg-rose-900/60 border border-rose-500/30 text-sm font-bold text-rose-400 transition-colors cursor-pointer text-center">
            🚪 Прервать рейс и выйти
          </button>
        </div>

        <button onclick={() => { playClickSound(); isSettingsOpen = false; }} class="w-full mt-2 p-3.5 rounded-xl bg-gradient-to-r from-amber-600 to-amber-500 text-stone-950 text-sm font-bold shadow-lg shadow-amber-500/20 cursor-pointer">
          ▶ Вернуться в вагон
        </button>
      </div>
    </div>
  {/if}

  <SeatMapModal isOpen={isSeatMapOpen} onClose={() => { isSeatMapOpen = false; }} />
  <ShiftDebriefModal isOpen={isDebriefOpen} onClose={() => { isDebriefOpen = false; }} />

  {#if trainWorld.isPhaseTransitioning}
    <div transition:fade={{ duration: 600 }} class="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-[#050505] text-amber-400">
      <div class="text-4xl mb-6">🚄</div>
      <h2 class="text-2xl font-bold tracking-widest uppercase text-white mb-4">В пути...</h2>
      <p class="text-xl text-[#a39e95] font-mono">{trainWorld.timeSkippedText}</p>
    </div>
  {/if}
</div>

<style>
  .cabin-viewport { position: relative; width: 100%; height: 100%; display: flex; flex-direction: column; overflow: hidden; background-color: #0f0e0d; }
  @media (min-width: 768px) { .cabin-viewport { display: flex; flex-direction: row; align-items: center; justify-content: center; padding: 0.5rem; } }

  .hud-top-bar { position: absolute; top: max(0.75rem, env(safe-area-inset-top)); left: 0.75rem; right: 0.75rem; z-index: 35; display: flex; align-items: center; justify-content: space-between; pointer-events: none; }
  .hud-top-bar > * { pointer-events: auto; }
  @media (min-width: 768px) { .hud-top-bar { top: 1.25rem; left: 1.5rem; right: 1.5rem; max-width: 96vw; margin: 0 auto; } }

  /* СТРЕЛКИ НАВИГАЦИИ (ВИДИМЫ ТОЛЬКО НА ТЕЛЕФОНАХ) */
  .pan-arrow { position: absolute; top: 40%; transform: translateY(-50%); z-index: 40; width: 44px; height: 44px; background: rgba(0, 0, 0, 0.4); color: white; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; cursor: pointer; backdrop-filter: blur(4px); pointer-events: auto; }
  .pan-arrow:active { background: rgba(0, 0, 0, 0.7); }
  .left-arrow { left: 0.5rem; }
  .right-arrow { right: 0.5rem; }

  /* АДАПТИВНЫЙ ФОН КАБИНЫ */
  .scene-scroll-area { flex: 1 1 0%; min-height: 0; width: 100%; overflow-x: auto; overflow-y: hidden; position: relative; display: flex; align-items: center; justify-content: flex-start; touch-action: pan-x; -webkit-overflow-scrolling: touch; background-color: #050505; }
  .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
  .hide-scrollbar::-webkit-scrollbar { display: none; }

  .scene-container { position: relative; display: inline-block; max-width: 96vw; max-height: 84vh; border-radius: 1rem; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8); background-color: #000; }
  .base-image { display: block; max-height: 84vh; max-width: 96vw; width: auto; height: auto; object-fit: contain; user-select: none; }
  .passenger-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: contain; pointer-events: none; user-select: none; }

  @media (max-width: 767px) {
    .scene-scroll-area { position: absolute; top: 10vh; height: 60vh; width: 100vw; align-items: flex-start; }
    .scene-container { height: 100%; max-height: none; max-width: none; width: auto; aspect-ratio: 1671 / 941; border-radius: 0; box-shadow: none; flex-shrink: 0; }
    .base-image { width: 100%; height: 100%; max-width: none; max-height: none; object-fit: fill; }
    .passenger-overlay { width: 100%; height: 100%; max-width: none; max-height: none; object-fit: fill; }
    .ambient-sway { animation: swayPan 14s ease-in-out infinite alternate; will-change: transform; }
    .scene-scroll-area:active .ambient-sway { animation-play-state: paused; }
    @keyframes swayPan { 0% { transform: translateX(-1.2%); } 100% { transform: translateX(1.2%); } }
  }

  /* === ИСПРАВЛЕНИЕ: НИЖНЯЯ ПАНЕЛЬ ПРИПОДНЯТА ОТ КРАЯ ЭКРАНА И ИМЕЕТ ОТСТУПЫ ПО БОКАМ === */
  .bottom-ui-panel { position: absolute; bottom: max(1.5rem, env(safe-area-inset-bottom)); left: 50%; transform: translateX(-50%); width: 100%; max-width: 48rem; z-index: 50; display: flex; flex-direction: column; align-items: center; pointer-events: none; padding: 0 0.75rem; }

  /* Универсальная кнопка действия */
  .main-action-btn { width: 100%; max-width: 24rem; padding: 0.75rem 1.25rem; border-radius: 1rem; font-weight: 800; font-size: 0.875rem; color: #fff; background-image: linear-gradient(to right, var(--tw-gradient-stops)); border-width: 1px; box-shadow: 0 10px 20px -5px rgba(0,0,0,0.5); cursor: pointer; transition: all 0.2s ease; display: flex; align-items: center; justify-content: center; gap: 0.5rem; }
  .main-action-btn:active { transform: scale(0.98); }

  /* === ИСПРАВЛЕНИЕ: ОБОЛОЧКА ДИАЛОГА ПРИПОДНЯТА ОТ КРАЯ ЭКРАНА === */
  .dialogue-wrapper { position: absolute; bottom: max(1rem, env(safe-area-inset-bottom)); left: 50%; transform: translateX(-50%); width: 100%; max-width: 54rem; z-index: 30; pointer-events: none; padding: 0 0.5rem; }
  @media (max-width: 767px) { .dialogue-wrapper { pointer-events: auto; } }

  /* Остальные классы HUD */
  .aisle-call-badge { position: absolute; z-index: 25; display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.75rem; border-radius: 0.5rem; background: linear-gradient(135deg, rgba(244, 63, 94, 0.95), rgba(225, 29, 72, 0.95)); border: 1px solid rgba(254, 205, 211, 0.9); color: #ffffff; font-size: 0.75rem; font-weight: bold; box-shadow: 0 8px 20px -3px rgba(225, 29, 72, 0.6); cursor: pointer; white-space: nowrap; }
  .call-ping { position: absolute; top: -3px; right: -3px; width: 10px; height: 10px; border-radius: 9999px; background-color: #f43f5e; animation: ping 1.5s infinite; }
  @keyframes ping { 75%, 100% { transform: scale(2); opacity: 0; } }

  .aisle-phase-banner { position: relative; z-index: 25; }
  .phase-banner-content { display: flex; align-items: center; gap: 0.4rem; padding: 0.35rem 0.6rem; border-radius: 0.5rem; background: rgba(20, 18, 16, 0.92); backdrop-filter: blur(10px); border: 1px solid #3d3831; color: #f5f3ef; font-size: 0.6875rem; box-shadow: 0 4px 15px rgba(0,0,0,0.6); }
  .phase-round { border-color: rgba(245, 158, 11, 0.4); }
  .phase-cruise { border-color: rgba(59, 130, 246, 0.4); background: rgba(15, 23, 42, 0.92); }
  .phase-warning { border-color: rgba(245, 158, 11, 0.8); background: rgba(45, 30, 15, 0.95); }
  .phase-arrival { border-color: rgba(16, 185, 129, 0.5); background: rgba(10, 30, 20, 0.92); }
  .phase-pulse-dot { width: 6px; height: 6px; border-radius: 50%; background-color: #3b82f6; animation: pulse 1.5s infinite; }

  .top-actions-cluster { position: relative; z-index: 25; display: flex; align-items: center; gap: 0.4rem; }
  .seat-map-trigger-btn { display: flex; align-items: center; justify-content: center; gap: 0.4rem; padding: 0.35rem 0.6rem; border-radius: 0.5rem; background: rgba(26, 24, 22, 0.9); border: 1px solid #3d3831; color: #f5f3ef; font-size: 0.6875rem; font-weight: 600; cursor: pointer; backdrop-filter: blur(10px); }
  .seat-map-trigger-btn:hover { background: rgba(40, 36, 32, 0.95); border-color: #f59e0b; color: #f59e0b; }
  .trigger-alert-badge { position: relative; display: inline-flex; align-items: center; justify-content: center; padding: 0.1rem 0.35rem; border-radius: 999px; background: #e11d48; color: #fff; font-size: 0.6rem; font-weight: 700; line-height: 1; }
  .trigger-alert-ping { position: absolute; inset: -2px; border-radius: 999px; background: #f43f5e; opacity: 0.75; animation: ping 1.5s infinite; }

  .seat-top-bar { position: relative; width: 100%; z-index: 25; display: flex; align-items: center; justify-content: center; pointer-events: none; }
  .seat-top-bar > * { pointer-events: auto; }
  .seat-stepper-mini { display: flex; align-items: center; gap: 0.35rem; background: rgba(20, 18, 16, 0.92); border: 1px solid #3d3831; padding: 0.25rem 0.4rem; border-radius: 0.625rem; }
  .stepper-mini-btn { padding: 0.3rem 0.65rem; border-radius: 0.375rem; background: #23201c; border: 1px solid #3d3831; color: #d6d3d1; font-size: 0.75rem; font-weight: 600; cursor: pointer; }
  .stepper-mini-seat { padding: 0.3rem 0.65rem; border-radius: 0.375rem; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); color: #fbbf24; font-size: 0.75rem; font-weight: 700; cursor: pointer; }

  .station-toast-overlay { position: absolute; top: 3.5rem; left: 50%; transform: translateX(-50%); z-index: 50; pointer-events: none; max-width: 90vw; }
  .toast-card { display: flex; flex-direction: column; align-items: center; gap: 0.2rem; padding: 0.5rem 1rem; border-radius: 0.75rem; background: rgba(20, 18, 16, 0.95); border: 1px solid rgba(245, 158, 11, 0.6); text-align: center; color: #f5f3ef; }
  .toast-title { font-size: 0.8rem; font-weight: 700; color: #f59e0b; }
  .toast-subtitle { font-size: 0.7rem; color: #d6d3cd; }

  /* Параллакс окна */
  .window-viewport { position: absolute; top: 0; bottom: 0; width: 50%; z-index: 1; overflow: hidden; pointer-events: none; }
  .left-viewport { left: 0; }
  .right-viewport { right: 0; transform: scaleX(-1); }
  .parallax-layer { position: absolute; inset: 0; background-repeat: repeat-x; animation: flowLeft linear infinite; animation-play-state: paused; }
  .parallax-layer.is-moving { animation-play-state: running; }
  .sky-layer { z-index: 1; background-image: url('/assets/bg_sky.jpg'); background-size: auto 100%; background-position: 0 0; animation-duration: 30s; }
  .ground-layer { z-index: 2; top: 35%; background-image: url('/assets/bg_bottom.png'); background-size: auto 100%; background-position: 0 bottom; animation-duration: 15s; }
  @keyframes flowLeft { from { background-position-x: 0; } to { background-position-x: -2000px; } }
  .cabin-overlay { position: relative; z-index: 2; }
  .high-speed-shake { animation: cabinShake 0.15s infinite ease-in-out alternate; }
  @keyframes cabinShake { 0% { transform: translateY(0); } 100% { transform: translateY(0.75px); } }
  .station-platform-layer { position: absolute; inset: 0; z-index: 1; background-image: url('/assets/platform_station.jpg'); background-size: cover; background-position: center; opacity: 0; transition: opacity 1.5s ease-in-out; pointer-events: none; }
  .station-platform-layer.platform-visible { opacity: 1; }
</style>