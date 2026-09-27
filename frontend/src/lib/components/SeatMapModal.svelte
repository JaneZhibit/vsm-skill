<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import { cabinState } from '../stores/cabinState.svelte';
  import { physicsState } from '../stores/trainPhysics.svelte';
  import type { PassengerSeat } from '../config/cabinConfig';
  import { playClickSound, playSuccessSound } from '../utils/audio';

  interface Props {
    isOpen: boolean;
    onClose: () => void;
  }

  let { isOpen, onClose }: Props = $props();

  let currentSeat = $derived(cabinState.selectedSeat);

  function handleSelect(seat: PassengerSeat) {
    playClickSound();
    cabinState.selectSeat(seat.id);
  }

  function handleInspect() {
    if (!currentSeat) return;
    playClickSound();
    cabinState.inspectSeat(currentSeat.id);
    onClose();
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Escape') onClose();
  }

  onMount(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  });

  function getSeat(row: number, letter: 'A' | 'B' | 'C' | 'D'): PassengerSeat | undefined {
    return cabinState.seats.find((s) => s.row === row && s.letter === letter);
  }

  function isRowWithIncident(row: number): boolean {
    return cabinState.seats.some(
      (s) => s.row === row && s.isOccupied && s.activeIncident != null && (typeof s.activeIncident === 'string' || s.activeIncident.phase !== 'passive')
    );
  }

  const rows = Array.from({ length: 12 }, (_, i) => i + 1);
</script>

{#if isOpen}
  <div class="modal-backdrop" transition:fade={{ duration: 150 }} onclick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
    <div class="modal-card flex flex-col min-h-0" transition:scale={{ duration: 200, start: 0.95 }}>

      <!-- ШАПКА -->
      <div class="modal-header shrink-0">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 w-full">
          <div>
            <div class="train-badge mb-1"><span class="badge-dot"></span><span>ВСМ-1 • Поезд № 754</span></div>
            <h2 class="header-title">Вг {physicsState.wagonNumber} <span class="class-tag">«{physicsState.wagonType}»</span></h2>
          </div>
          <div class="header-stats w-full md:w-auto">
            <div class="stat-pill flex-1 md:flex-none justify-center"><span class="stat-label hidden md:inline">Загрузка:</span><span class="stat-value text-stone-200">{cabinState.occupiedSeatsCount}/48</span></div>
            <div class="stat-pill flex-1 md:flex-none justify-center"><span class="stat-label hidden md:inline">Проверено:</span><span class="stat-value text-emerald-400">{cabinState.validatedCount}/{cabinState.occupiedSeatsCount}</span></div>
            {#if cabinState.alertSeatsCount > 0}
              <div class="stat-pill alert flex-1 md:flex-none justify-center"><span class="stat-dot animate-ping"></span><span class="stat-value text-rose-400 font-bold">{cabinState.alertSeatsCount}</span></div>
            {/if}
            <button class="close-btn shrink-0 ml-1" onclick={onClose}>✕</button>
          </div>
        </div>
      </div>

      <!-- ТЕЛО С ВЕРТИКАЛЬНЫМ СКРОЛЛОМ -->
      <div class="modal-body flex-1 overflow-y-auto hide-scrollbar bg-[#0f0e0d]">
        <div class="train-direction-bar mb-3">
          <span class="direction-item">← Хвост</span><span class="direction-divider"></span><span class="direction-arrow">Движение ➔</span><span class="direction-divider"></span><span class="direction-item font-semibold text-amber-400">Голова →</span>
        </div>

        {#snippet SeatBeacon(seat: PassengerSeat)}
          {#if seat.isOccupied}
            {#if seat.activeIncident != null}
              {#if typeof seat.activeIncident === 'object' && seat.activeIncident.phase === 'passive'}
                <span class="beacon-observe animate-pulse opacity-60 text-stone-300">👁️</span>
              {:else}
                <span class="beacon-call animate-bounce text-rose-500">🔔</span>
              {/if}
            {:else if seat.condition === 'annoyed'}
              <span class="beacon-call">🔔</span>
            {:else if seat.condition === 'sick'}
              <span class="beacon-sick">🩺</span>
            {:else if seat.condition === 'sleeping'}
              <span class="beacon-pending text-indigo-400">💤</span>
            {:else if seat.condition === 'drunk'}
              <span class="beacon-pending text-amber-500">🍺</span>
            {:else if seat.ticketStatus === 'validated'}
              <span class="beacon-ok">✓</span>
            {:else}
              <span class="beacon-pending">•</span>
            {/if}
          {/if}
        {/snippet}

        {#snippet SeatCell(seat: PassengerSeat | undefined)}
          {#if seat}
            <button class="seat-btn" class:occupied={seat.isOccupied} class:selected={currentSeat?.id === seat.id} class:validated={seat.isOccupied && seat.ticketStatus === 'validated'} class:pending={seat.isOccupied && seat.ticketStatus === 'not_checked'} class:alert={seat.isOccupied && seat.activeIncident != null && (typeof seat.activeIncident === 'string' || seat.activeIncident.phase !== 'passive')} onclick={() => handleSelect(seat)}>
              <span class="seat-id">{seat.id}</span>
              <div class="seat-indicator-box">{@render SeatBeacon(seat)}</div>
            </button>
          {:else}
            <div></div>
          {/if}
        {/snippet}

        <!-- ВЕРТИКАЛЬНАЯ СЕТКА -->
        <div class="cabin-grid-wrapper max-w-md mx-auto">
          <div class="grid grid-cols-[1fr_1fr_24px_1fr_1fr] gap-x-2 gap-y-1.5 items-center">

            <!-- Заголовки колонок -->
            <div class="col-header">A<span class="text-[8px] block font-normal text-stone-500">ОКНО</span></div>
            <div class="col-header">B<span class="text-[8px] block font-normal text-stone-500">ПРОХОД</span></div>
            <div></div>
            <div class="col-header">C<span class="text-[8px] block font-normal text-stone-500">ПРОХОД</span></div>
            <div class="col-header">D<span class="text-[8px] block font-normal text-stone-500">ОКНО</span></div>

            <!-- Ряды -->
            {#each rows as r}
              {@const seatA = getSeat(r, 'A')}
              {@const seatB = getSeat(r, 'B')}
              {@const seatC = getSeat(r, 'C')}
              {@const seatD = getSeat(r, 'D')}

              {@render SeatCell(seatA)}
              {@render SeatCell(seatB)}

              <!-- Маркер центрального прохода (номер ряда) -->
              <div class="flex items-center justify-center text-[9px] font-mono text-amber-600/60 font-bold" class:row-alert={isRowWithIncident(r)}>
                {r}
              </div>

              {@render SeatCell(seatC)}
              {@render SeatCell(seatD)}
            {/each}
          </div>
        </div>

        <div class="scheme-legend max-w-md mx-auto mt-4">
          <div class="legend-item"><span class="legend-box empty"></span><span>Свободно</span></div>
          <div class="legend-item"><span class="legend-box pending"></span><span>Вал.</span></div>
          <div class="legend-item"><span class="legend-box validated"></span><span>Ок</span></div>
          <div class="legend-item"><span class="legend-box alert"></span><span>Вызов</span></div>
          <div class="legend-item"><span class="legend-box selected"></span><span>Выбор</span></div>
        </div>
      </div>

      <!-- ПОДВАЛ: КАРТОЧКА ПАССАЖИРА -->
      <div class="modal-footer shrink-0 bg-[#1a1816] border-t border-[#2d2924] p-3 md:p-4">
        <div class="passenger-card">
          {#if currentSeat}
            <div class="flex items-center gap-3 md:gap-4 w-full">
              <div class="seat-big-tag shrink-0 w-12 text-center">{currentSeat.id}</div>
              <div class="flex-1 min-w-0 flex flex-col gap-0.5">
                <div class="flex items-center justify-between">
                  <span class="p-name text-xs md:text-sm truncate pr-2">
                    {currentSeat.isOccupied ? (currentSeat.passenger?.full_name || currentSeat.passengerName) : 'Свободное место'}
                  </span>
                  {#if currentSeat.isOccupied}
                    <span class="text-[9px] px-1.5 py-0.5 rounded bg-[#282420] text-stone-300 whitespace-nowrap">{currentSeat.gender === 'f' ? '♀ Жен' : '♂ Муж'}</span>
                  {/if}
                </div>
                <div class="flex items-center justify-between mt-1">
                  {#if currentSeat.isOccupied}
                    <span class="text-[10px] text-stone-400 truncate">📍 Мск ➔ <strong class="text-amber-300">{currentSeat.destination}</strong></span>
                    <span class="text-[9px] px-1.5 py-0.5 rounded font-bold whitespace-nowrap {currentSeat.ticketStatus === 'validated' ? 'text-emerald-400 bg-emerald-950/40 border border-emerald-500/30' : 'text-amber-400 bg-amber-950/30 border border-amber-500/30'}">
                      {currentSeat.ticketStatus === 'validated' ? '✓ Билет' : '⏳ Ждет'}
                    </span>
                  {:else}
                    <span class="text-stone-500 text-[10px]">Место свободно</span>
                  {/if}
                </div>
              </div>
              <button class="shrink-0 px-4 py-3 rounded-xl font-bold text-xs cursor-pointer bg-gradient-to-r from-amber-600 to-amber-500 text-stone-950 shadow-md" onclick={handleInspect}>
                Подойти
              </button>
            </div>
          {/if}
        </div>
      </div>

    </div>
  </div>
{/if}

<style>
  .modal-backdrop { position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center; background: rgba(10, 9, 8, 0.85); backdrop-filter: blur(8px); padding: max(1rem, env(safe-area-inset-top)) 0.5rem max(1rem, env(safe-area-inset-bottom)) 0.5rem; }

  .modal-card { width: 100%; max-width: 460px; max-height: 100%; background: #141210; border: 1px solid #2d2924; border-radius: 1rem; overflow: hidden; }

  .modal-header { padding: 0.75rem 1rem; background: #1a1816; border-bottom: 1px solid #2d2924; }
  .train-badge { display: flex; align-items: center; gap: 0.4rem; font-size: 0.6rem; color: #f59e0b; font-weight: bold; text-transform: uppercase; }
  .badge-dot { width: 5px; height: 5px; border-radius: 9999px; background-color: #f59e0b; }
  .header-title { color: #f5f3ef; font-weight: 800; font-size: 1rem; display: flex; align-items: center; gap: 0.5rem; }
  .class-tag { font-size: 0.65rem; padding: 0.15rem 0.4rem; border-radius: 0.25rem; background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.3); color: #f59e0b; font-weight: 600; }

  .header-stats { display: flex; gap: 0.4rem; align-items: center; }
  .stat-pill { display: flex; align-items: center; gap: 0.25rem; padding: 0.25rem 0.5rem; background: #23201c; border: 1px solid #3d3831; border-radius: 0.5rem; font-size: 0.7rem; }
  .stat-pill.alert { background: rgba(225, 29, 72, 0.15); border-color: rgba(244, 63, 94, 0.5); }
  .stat-dot { width: 6px; height: 6px; border-radius: 9999px; background-color: #f43f5e; }
  .close-btn { width: 28px; height: 28px; border-radius: 0.5rem; background: #23201c; border: 1px solid #3d3831; color: #a8a29e; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; }

  .modal-body { padding: 1rem; }
  .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
  .hide-scrollbar::-webkit-scrollbar { display: none; }

  .train-direction-bar { display: flex; align-items: center; justify-content: space-between; padding: 0.3rem 0.75rem; background: #1a1816; border: 1px solid #2d2924; border-radius: 0.5rem; font-size: 0.65rem; color: #a8a29e; }
  .direction-divider { flex-grow: 1; height: 1px; background: #2d2924; margin: 0 0.5rem; }

  .col-header { text-align: center; font-size: 0.8rem; font-weight: 800; color: #78716c; line-height: 1.1; margin-bottom: 0.25rem; }

  .seat-btn { position: relative; height: 32px; display: flex; align-items: center; justify-content: center; background: #1a1816; border: 1px solid #2d2924; border-radius: 0.4rem; cursor: pointer; transition: all 0.1s; }
  .seat-btn.occupied { background: #201d19; border-color: #3d3831; color: #d6d3d1; }
  .seat-btn.pending { border-color: rgba(245, 158, 11, 0.4); background: rgba(245, 158, 11, 0.08); }
  .seat-btn.validated { border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.1); }
  .seat-btn.alert { border-color: #f43f5e; background: rgba(225, 29, 72, 0.25); animation: alertPulse 1.8s infinite; }
  .seat-btn.selected { border-color: #f59e0b; background: rgba(245, 158, 11, 0.25); box-shadow: 0 0 0 1px #f59e0b; color: white; transform: scale(1.05); z-index: 10; }

  .seat-id { font-size: 0.65rem; font-weight: 700; font-family: ui-monospace, SFMono-Regular, monospace; }
  .seat-indicator-box { position: absolute; top: -6px; right: -6px; width: 14px; height: 14px; display: flex; align-items: center; justify-content: center; }

  .scheme-legend { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; font-size: 0.6rem; color: #a8a29e; }
  .legend-item { display: flex; align-items: center; gap: 0.25rem; }
  .legend-box { width: 10px; height: 10px; border-radius: 2px; border: 1px solid #3d3831; background: #1a1816; }
  .legend-box.pending { border-color: #f59e0b; background: rgba(245, 158, 11, 0.2); }
  .legend-box.validated { border-color: #10b981; background: rgba(16, 185, 129, 0.25); }
  .legend-box.alert { border-color: #f43f5e; background: rgba(225, 29, 72, 0.4); }
  .legend-box.selected { border-color: #f59e0b; background: #f59e0b; }

  .passenger-card { background: #0f0e0d; border: 1px solid #3d3831; border-radius: 0.75rem; padding: 0.75rem; width: 100%; }
  .seat-big-tag { font-size: 1.5rem; font-weight: 900; color: white; font-family: ui-monospace, SFMono-Regular, monospace; line-height: 1; }
  .p-name { font-weight: 800; color: white; }

  .row-alert { color: #f43f5e !important; animation: alertPulseText 1.8s infinite; }

  .beacon-call { font-size: 0.65rem; animation: bounce 1.5s infinite; }
  .beacon-ok { font-size: 0.5rem; color: #34d399; font-weight: 900; background: #0f0e0d; border-radius: 50%; padding: 2px; border: 1px solid #10b981; }
  .beacon-pending { font-size: 0.7rem; color: #f59e0b; line-height: 0.5; }
  .beacon-observe { font-size: 0.7rem; }

  @keyframes alertPulse { 0%, 100% { border-color: #f43f5e; } 50% { border-color: #fda4af; } }
  @keyframes alertPulseText { 0%, 100% { color: #f43f5e; } 50% { color: #fda4af; } }
  @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-2px); } }
</style>