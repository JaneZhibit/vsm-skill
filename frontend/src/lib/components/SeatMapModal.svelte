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

  function handleValidate() {
    if (!currentSeat || !currentSeat.isOccupied) return;
    playSuccessSound();
    cabinState.validateCurrentSeat(currentSeat.id);
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
  <div class="modal-backdrop" transition:fade={{ duration: 200 }} onclick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
    <div class="modal-card" transition:scale={{ duration: 220, start: 0.95 }}>
      <div class="modal-header">
        <div class="header-left">
          <div class="train-badge"><span class="badge-dot"></span><span>ВСМ-1 «Белый кречет» • Поезд № 754</span></div>
          <h2 class="header-title">Схема вагона № {physicsState.wagonNumber} <span class="class-tag">Класс «{physicsState.wagonType}»</span></h2>
        </div>
        <div class="header-stats">
          <div class="stat-pill"><span class="stat-label">Загрузка:</span><span class="stat-value text-stone-200">{cabinState.occupiedSeatsCount}/48 ({Math.round((cabinState.occupiedSeatsCount / 48) * 100)}%)</span></div>
          <div class="stat-pill"><span class="stat-label">Проверено:</span><span class="stat-value text-emerald-400">{cabinState.validatedCount}/{cabinState.occupiedSeatsCount}</span></div>
          {#if cabinState.alertSeatsCount > 0}
            <div class="stat-pill alert"><span class="stat-dot animate-ping"></span><span class="stat-label">Внимание:</span><span class="stat-value text-rose-400 font-bold">{cabinState.alertSeatsCount}</span></div>
          {/if}
          <button class="close-btn" onclick={onClose}>✕</button>
        </div>
      </div>

      <div class="modal-body">
        <div class="train-direction-bar">
          <span class="direction-item">← Хвост (Вг 04)</span><span class="direction-divider"></span><span class="direction-arrow">Движение ➔</span><span class="direction-divider"></span><span class="direction-item font-semibold text-amber-400">Голова (Вг 02) →</span>
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

        <div class="cabin-grid-wrapper">
          <div class="cabin-grid">
            <!-- Ряд A -->
            <div class="grid-row">
              <div class="row-label">A (окно)</div>
              {#each rows as r}
                {@const seat = getSeat(r, 'A')}
                {#if seat}
                  <button class="seat-btn" class:occupied={seat.isOccupied} class:selected={currentSeat?.id === seat.id} class:validated={seat.isOccupied && seat.ticketStatus === 'validated'} class:pending={seat.isOccupied && seat.ticketStatus === 'not_checked'} class:alert={seat.isOccupied && seat.activeIncident != null && (typeof seat.activeIncident === 'string' || seat.activeIncident.phase !== 'passive')} class:row-alert={isRowWithIncident(r)} onclick={() => handleSelect(seat)}>
                    <span class="seat-id">{seat.id}</span>{@render SeatBeacon(seat)}
                  </button>
                {/if}
              {/each}
            </div>
            <!-- Ряд B -->
            <div class="grid-row">
              <div class="row-label">B (проход)</div>
              {#each rows as r}
                {@const seat = getSeat(r, 'B')}
                {#if seat}
                  <button class="seat-btn" class:occupied={seat.isOccupied} class:selected={currentSeat?.id === seat.id} class:validated={seat.isOccupied && seat.ticketStatus === 'validated'} class:pending={seat.isOccupied && seat.ticketStatus === 'not_checked'} class:alert={seat.isOccupied && seat.activeIncident != null && (typeof seat.activeIncident === 'string' || seat.activeIncident.phase !== 'passive')} class:row-alert={isRowWithIncident(r)} onclick={() => handleSelect(seat)}>
                    <span class="seat-id">{seat.id}</span>{@render SeatBeacon(seat)}
                  </button>
                {/if}
              {/each}
            </div>
            <!-- Проход -->
            <div class="aisle-row">
              <div class="row-label aisle-text">Проход</div>
              {#each rows as r}
                <div class="aisle-marker" class:row-alert={isRowWithIncident(r)}>
                  <span class="aisle-num">{r}</span><span class="aisle-arrow">›</span>
                </div>
              {/each}
            </div>
            <!-- Ряд C -->
            <div class="grid-row">
              <div class="row-label">C (проход)</div>
              {#each rows as r}
                {@const seat = getSeat(r, 'C')}
                {#if seat}
                  <button class="seat-btn" class:occupied={seat.isOccupied} class:selected={currentSeat?.id === seat.id} class:validated={seat.isOccupied && seat.ticketStatus === 'validated'} class:pending={seat.isOccupied && seat.ticketStatus === 'not_checked'} class:alert={seat.isOccupied && seat.activeIncident != null && (typeof seat.activeIncident === 'string' || seat.activeIncident.phase !== 'passive')} class:row-alert={isRowWithIncident(r)} onclick={() => handleSelect(seat)}>
                    <span class="seat-id">{seat.id}</span>{@render SeatBeacon(seat)}
                  </button>
                {/if}
              {/each}
            </div>
            <!-- Ряд D -->
            <div class="grid-row">
              <div class="row-label">D (окно)</div>
              {#each rows as r}
                {@const seat = getSeat(r, 'D')}
                {#if seat}
                  <button class="seat-btn" class:occupied={seat.isOccupied} class:selected={currentSeat?.id === seat.id} class:validated={seat.isOccupied && seat.ticketStatus === 'validated'} class:pending={seat.isOccupied && seat.ticketStatus === 'not_checked'} class:alert={seat.isOccupied && seat.activeIncident != null && (typeof seat.activeIncident === 'string' || seat.activeIncident.phase !== 'passive')} class:row-alert={isRowWithIncident(r)} onclick={() => handleSelect(seat)}>
                    <span class="seat-id">{seat.id}</span>{@render SeatBeacon(seat)}
                  </button>
                {/if}
              {/each}
            </div>
          </div>
        </div>

        <div class="scheme-legend">
          <div class="legend-item"><span class="legend-box empty"></span><span>Свободно</span></div>
          <div class="legend-item"><span class="legend-box pending"></span><span>Требует валидации</span></div>
          <div class="legend-item"><span class="legend-box validated"></span><span>Проверено</span></div>
          <div class="legend-item"><span class="legend-box alert"></span><span>Вызов</span></div>
          <div class="legend-item"><span class="legend-box selected"></span><span>Выбор</span></div>
        </div>

        <div class="passenger-card">
          {#if currentSeat}
            <div class="card-clean-layout">
              <div class="seat-big-tag">{currentSeat.id}</div>
              <div class="seat-clean-info">
                <div class="passenger-name-row">
                  {#if currentSeat.isOccupied}
                    <span class="p-name">{currentSeat.passenger?.full_name || currentSeat.passengerName}</span>
                    <span class="gender-pill">{currentSeat.gender === 'f' ? '♀ Жен' : '♂ Муж'}</span>
                  {:else}
                    <span class="text-stone-400 italic">Свободное место</span>
                  {/if}
                </div>
                <div class="passenger-route-row">
                  {#if currentSeat.isOccupied}
                    <span class="route-tag">📍 Москва ➔ <strong class="text-amber-300">{currentSeat.destination}</strong></span>
                    <span class="ticket-status-pill {currentSeat.ticketStatus === 'validated' ? 'valid' : 'pending'}">
                      {currentSeat.ticketStatus === 'validated' ? '✓ Подтверждено' : '⏳ Ожидает проверки'}
                    </span>
                  {:else}
                    <span class="text-stone-500 text-xs">Место свободно на всем маршруте</span>
                  {/if}
                </div>
              </div>
              <div class="seat-clean-action">
                <button class="action-btn inspect" onclick={handleInspect}>🚶 Подойти ➔</button>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  /* Стили остаются ровно такими же, как были в твоем оригинальном файле!
     Они полностью совместимы с этой новой разметкой. */
  .modal-backdrop { position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center; background: rgba(10, 9, 8, 0.85); backdrop-filter: blur(10px); padding: 1rem; }
  .modal-card { width: 100%; max-width: 980px; background: #141210; border: 1px solid #2d2924; border-radius: 1rem; }
  .modal-header { display: flex; align-items: center; justify-content: space-between; padding: 1.1rem 1.5rem; background: #1a1816; border-bottom: 1px solid #2d2924; }
  .train-badge { display: flex; align-items: center; gap: 0.5rem; font-size: 0.6875rem; color: #f59e0b; }
  .badge-dot { width: 6px; height: 6px; border-radius: 9999px; background-color: #f59e0b; }
  .header-title { color: #f5f3ef; font-weight: 700; font-size: 1.125rem; display: flex; align-items: center; gap: 0.6rem; }
  .class-tag { font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: 0.375rem; background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.3); color: #f59e0b; }
  .header-stats { display: flex; gap: 0.75rem; align-items: center;}
  .stat-pill { display: flex; align-items: center; gap: 0.35rem; padding: 0.35rem 0.75rem; background: #23201c; border: 1px solid #3d3831; border-radius: 0.5rem; font-size: 0.75rem; }
  .stat-pill.alert { background: rgba(225, 29, 72, 0.15); border-color: rgba(244, 63, 94, 0.5); }
  .stat-dot { width: 6px; height: 6px; border-radius: 9999px; background-color: #f43f5e; }
  .close-btn { width: 32px; height: 32px; border-radius: 0.5rem; background: #23201c; border: 1px solid #3d3831; color: #a8a29e; cursor: pointer; }
  .modal-body { padding: 1.25rem 1.5rem; display: flex; flex-direction: column; gap: 1rem; }
  .train-direction-bar { display: flex; align-items: center; justify-content: space-between; padding: 0.4rem 1rem; background: #1a1816; border: 1px solid #2d2924; border-radius: 0.5rem; font-size: 0.75rem; color: #a8a29e; }
  .direction-divider { flex-grow: 1; height: 1px; background: #2d2924; margin: 0 1rem; }
  .cabin-grid-wrapper { background: #0f0e0d; border: 1px solid #2d2924; border-radius: 0.75rem; padding: 1rem; overflow-x: auto; }
  .cabin-grid { display: flex; flex-direction: column; gap: 0.45rem; min-width: 780px; }
  .grid-row, .aisle-row { display: grid; grid-template-columns: 85px repeat(12, 1fr); gap: 0.4rem; align-items: center; }
  .row-label { font-size: 0.6875rem; color: #78716c; text-transform: uppercase; font-weight: 600; }
  .aisle-text { color: #f59e0b; }
  .seat-btn { height: 44px; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #1a1816; border: 1px solid #2d2924; border-radius: 0.375rem; cursor: pointer; }
  .seat-btn.occupied { background: #201d19; border-color: #3d3831; color: #d6d3d1; }
  .seat-btn.pending { border-color: rgba(245, 158, 11, 0.4); background: rgba(245, 158, 11, 0.06); }
  .seat-btn.validated { border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.08); }
  .seat-btn.alert { border-color: #f43f5e; background: rgba(225, 29, 72, 0.25); animation: alertPulse 1.8s infinite; }
  .seat-btn.selected { border-color: #f59e0b; background: rgba(245, 158, 11, 0.2); box-shadow: 0 0 0 2px #f59e0b; color: white; }
  .seat-id { font-size: 0.6875rem; font-weight: 700; }
  .scheme-legend { display: flex; gap: 1.25rem; font-size: 0.6875rem; color: #a8a29e; }
  .legend-item { display: flex; align-items: center; gap: 0.4rem; }
  .legend-box { width: 14px; height: 14px; border-radius: 3px; border: 1px solid #3d3831; background: #1a1816; }
  .legend-box.pending { border-color: #f59e0b; background: rgba(245, 158, 11, 0.2); }
  .legend-box.validated { border-color: #10b981; background: rgba(16, 185, 129, 0.25); }
  .legend-box.alert { border-color: #f43f5e; background: rgba(225, 29, 72, 0.4); }
  .legend-box.selected { border-color: #f59e0b; background: #f59e0b; }
  .passenger-card { background: #1a1816; border: 1px solid #2d2924; border-radius: 0.75rem; padding: 1.1rem; }
  .card-clean-layout { display: flex; align-items: center; gap: 1.25rem; }
  .seat-big-tag { font-size: 2rem; font-weight: bold; color: white; }
  .seat-clean-info { flex-grow: 1; display: flex; flex-direction: column; gap: 0.35rem; }
  .p-name { font-weight: 700; color: white; }
  .passenger-route-row { display: flex; gap: 0.75rem; font-size: 0.8125rem; color: #d6d3d1; }
  .ticket-status-pill { font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: 0.375rem; }
  .ticket-status-pill.valid { color: #34d399; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.35); }
  .ticket-status-pill.pending { color: #fbbf24; background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.3); }
  .action-btn { padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: 700; cursor: pointer; background: linear-gradient(135deg, #f59e0b, #d97706); color: black; border: 1px solid #fbbf24; }
  .aisle-marker { display: flex; align-items: center; justify-content: center; height: 20px; color: #78716c; font-size: 0.6875rem; }
  .beacon-call { font-size: 0.75rem; animation: bounce 1.5s infinite; }
  .beacon-ok { font-size: 0.625rem; color: #34d399; font-weight: bold; }
  .beacon-pending { font-size: 0.875rem; color: #f59e0b; line-height: 0.5; }
  .beacon-observe { font-size: 0.85rem; }
  @keyframes alertPulse { 0%, 100% { border-color: #f43f5e; } 50% { border-color: #fda4af; } }
  @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-2px); } }
</style>