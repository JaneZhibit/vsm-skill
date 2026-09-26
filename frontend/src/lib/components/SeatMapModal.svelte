<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import { trainWorld } from '../stores/trainWorld.svelte';
  import type { PassengerSeat } from '../config/cabinConfig';
  import { playClickSound, playSuccessSound } from '../utils/audio';

  interface Props {
    isOpen: boolean;
    onClose: () => void;
  }

  let { isOpen, onClose }: Props = $props();

  // Быстрый доступ к выбранному креслу
  let currentSeat = $derived(trainWorld.selectedSeat);

  function handleSelect(seat: PassengerSeat) {
    playClickSound();
    trainWorld.selectSeat(seat.id);
  }

  function handleInspect() {
    if (!currentSeat) return;
    playClickSound();
    trainWorld.inspectSeat(currentSeat.id);
    onClose();
  }

  function handleValidate() {
    if (!currentSeat || !currentSeat.isOccupied) return;
    playSuccessSound();
    trainWorld.validateCurrentSeat(currentSeat.id);
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      onClose();
    }
  }

  onMount(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  });

  // Получение кресла по ряду и букве
  function getSeat(row: number, letter: 'A' | 'B' | 'C' | 'D'): PassengerSeat | undefined {
    return trainWorld.seats.find((s) => s.row === row && s.letter === letter);
  }

  function isRowWithIncident(row: number): boolean {
    return trainWorld.seats.some(
      (s) =>
        s.row === row &&
        s.isOccupied &&
        s.activeIncident != null &&
        (typeof s.activeIncident === 'string' || s.activeIncident.phase !== 'passive')
    );
  }

  const rows = Array.from({ length: 12 }, (_, i) => i + 1);
</script>

{#if isOpen}
  <!-- Оверлей модального окна -->
  <div
    class="modal-backdrop"
    transition:fade={{ duration: 200 }}
    onclick={(e) => {
      if (e.target === e.currentTarget) onClose();
    }}
    onkeydown={(e) => {
      if (e.key === 'Escape') onClose();
    }}
    role="dialog"
    tabindex="-1"
    aria-modal="true"
    aria-labelledby="seatmap-title"
  >
    <div class="modal-card" transition:scale={{ duration: 220, start: 0.95 }}>
      <!-- Шапка модального окна -->
      <div class="modal-header">
        <div class="header-left">
          <div class="train-badge">
            <span class="badge-dot"></span>
            <span>ВСМ-1 «Белый кречет» • Поезд № 754</span>
          </div>
          <h2 id="seatmap-title" class="header-title">
            Схема вагона № {trainWorld.wagonNumber}
            <span class="class-tag">Класс «{trainWorld.wagonType}»</span>
          </h2>
        </div>

        <!-- Сводная статистика вагона -->
        <div class="header-stats">
          <div class="stat-pill" title="Занятые места">
            <span class="stat-label">Загрузка:</span>
            <span class="stat-value text-stone-200">
              {trainWorld.occupiedSeatsCount}/48 ({Math.round((trainWorld.occupiedSeatsCount / 48) * 100)}%)
            </span>
          </div>
          <div class="stat-pill" title="Проверено билетов">
            <span class="stat-label">Проверено:</span>
            <span class="stat-value text-emerald-400">
              {trainWorld.validatedCount}/{trainWorld.occupiedSeatsCount}
            </span>
          </div>
          {#if trainWorld.alertSeatsCount > 0}
            <div class="stat-pill alert" title="Требуют внимания проводника">
              <span class="stat-dot animate-ping"></span>
              <span class="stat-label">Внимание:</span>
              <span class="stat-value text-rose-400 font-bold">{trainWorld.alertSeatsCount}</span>
            </div>
          {/if}

          <!-- Кнопка закрытия -->
          <button class="close-btn" onclick={onClose} aria-label="Закрыть схему вагона">
            ✕
          </button>
        </div>
      </div>

      <!-- Основная область: Схема вагона 12 рядов 2+2 -->
      <div class="modal-body">
        <div class="train-direction-bar">
          <span class="direction-item">← Хвост состава (Вагон 04)</span>
          <span class="direction-divider"></span>
          <span class="direction-arrow">Направление движения ➔</span>
          <span class="direction-divider"></span>
          <span class="direction-item font-semibold text-amber-400">Голова состава (Вагон 02) →</span>
        </div>

        {#snippet SeatBeacon(seat: PassengerSeat)}
          {#if seat.isOccupied}
            {#if seat.activeIncident != null}
              {#if typeof seat.activeIncident === 'object' && seat.activeIncident.phase === 'passive'}
                <span class="beacon-observe animate-pulse opacity-60 text-stone-300" title="Что-то происходит">👁️</span>
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

        <!-- Сетка кресел вагона (горизонтальная раскладка) -->
        <div class="cabin-grid-wrapper">
          <div class="cabin-grid">
            <!-- Ряд мест A (у окна слева) -->
            <div class="grid-row">
              <div class="row-label">A (окно)</div>
              {#each rows as r}
                {@const seat = getSeat(r, 'A')}
                {#if seat}
                  <button
                    class="seat-btn"
                    class:occupied={seat.isOccupied}
                    class:selected={currentSeat?.id === seat.id}
                    class:validated={seat.isOccupied && seat.ticketStatus === 'validated'}
                    class:pending={seat.isOccupied && seat.ticketStatus === 'not_checked'}
                    class:alert={seat.isOccupied && seat.activeIncident != null && (typeof seat.activeIncident === 'string' || seat.activeIncident.phase !== 'passive')}
                    class:row-alert={isRowWithIncident(r)}
                    onclick={() => handleSelect(seat)}
                    title="{seat.id}: {seat.isOccupied ? (seat.passengerName || 'Пассажир') : 'Свободно'}"
                  >
                    <span class="seat-id">{seat.id}</span>
                    {@render SeatBeacon(seat)}
                  </button>
                {/if}
              {/each}
            </div>

            <!-- Ряд мест B (у прохода слева) -->
            <div class="grid-row">
              <div class="row-label">B (проход)</div>
              {#each rows as r}
                {@const seat = getSeat(r, 'B')}
                {#if seat}
                  <button
                    class="seat-btn"
                    class:occupied={seat.isOccupied}
                    class:selected={currentSeat?.id === seat.id}
                    class:validated={seat.isOccupied && seat.ticketStatus === 'validated'}
                    class:pending={seat.isOccupied && seat.ticketStatus === 'not_checked'}
                    class:alert={seat.isOccupied && seat.activeIncident != null && (typeof seat.activeIncident === 'string' || seat.activeIncident.phase !== 'passive')}
                    class:row-alert={isRowWithIncident(r)}
                    onclick={() => handleSelect(seat)}
                    title="{seat.id}: {seat.isOccupied ? (seat.passengerName || 'Пассажир') : 'Свободно'}"
                  >
                    <span class="seat-id">{seat.id}</span>
                    {@render SeatBeacon(seat)}
                  </button>
                {/if}
              {/each}
            </div>

            <!-- Центральный проход с номерами рядов -->
            <div class="aisle-row">
              <div class="row-label aisle-text">Проход</div>
              {#each rows as r}
                <div class="aisle-marker" class:row-alert={isRowWithIncident(r)}>
                  <span class="aisle-num">{r}</span>
                  <span class="aisle-arrow">›</span>
                </div>
              {/each}
            </div>

            <!-- Ряд мест C (у прохода справа) -->
            <div class="grid-row">
              <div class="row-label">C (проход)</div>
              {#each rows as r}
                {@const seat = getSeat(r, 'C')}
                {#if seat}
                  <button
                    class="seat-btn"
                    class:occupied={seat.isOccupied}
                    class:selected={currentSeat?.id === seat.id}
                    class:validated={seat.isOccupied && seat.ticketStatus === 'validated'}
                    class:pending={seat.isOccupied && seat.ticketStatus === 'not_checked'}
                    class:alert={seat.isOccupied && seat.activeIncident != null && (typeof seat.activeIncident === 'string' || seat.activeIncident.phase !== 'passive')}
                    class:row-alert={isRowWithIncident(r)}
                    onclick={() => handleSelect(seat)}
                    title="{seat.id}: {seat.isOccupied ? (seat.passengerName || 'Пассажир') : 'Свободно'}"
                  >
                    <span class="seat-id">{seat.id}</span>
                    {@render SeatBeacon(seat)}
                  </button>
                {/if}
              {/each}
            </div>

            <!-- Ряд мест D (у окна справа) -->
            <div class="grid-row">
              <div class="row-label">D (окно)</div>
              {#each rows as r}
                {@const seat = getSeat(r, 'D')}
                {#if seat}
                  <button
                    class="seat-btn"
                    class:occupied={seat.isOccupied}
                    class:selected={currentSeat?.id === seat.id}
                    class:validated={seat.isOccupied && seat.ticketStatus === 'validated'}
                    class:pending={seat.isOccupied && seat.ticketStatus === 'not_checked'}
                    class:alert={seat.isOccupied && seat.activeIncident != null && (typeof seat.activeIncident === 'string' || seat.activeIncident.phase !== 'passive')}
                    class:row-alert={isRowWithIncident(r)}
                    onclick={() => handleSelect(seat)}
                    title="{seat.id}: {seat.isOccupied ? (seat.passengerName || 'Пассажир') : 'Свободно'}"
                  >
                    <span class="seat-id">{seat.id}</span>
                    {@render SeatBeacon(seat)}
                  </button>
                {/if}
              {/each}
            </div>
          </div>
        </div>

        <!-- Легенда обозначений схемы -->
        <div class="scheme-legend">
          <div class="legend-item">
            <span class="legend-box empty"></span>
            <span>Свободно</span>
          </div>
          <div class="legend-item">
            <span class="legend-box pending"></span>
            <span>Требует валидации</span>
          </div>
          <div class="legend-item">
            <span class="legend-box validated"></span>
            <span>Билет проверен</span>
          </div>
          <div class="legend-item">
            <span class="legend-box alert"></span>
            <span>Вызов / Претензия</span>
          </div>
          <div class="legend-item">
            <span class="legend-box selected"></span>
            <span>Текущий выбор</span>
          </div>
        </div>

        <!-- Детальная карточка выбранного кресла / пассажира -->
        <div class="passenger-card">
          {#if currentSeat}
            <div class="card-clean-layout">
              <!-- Левая часть: Крупный номер места -->
              <div class="seat-big-tag">
                {currentSeat.id}
              </div>

              <!-- Центральная часть: ФИО, пол, маршрут, статус билета -->
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
                    <span class="route-tag">
                      📍 Москва ➔ <strong class="text-amber-300">{currentSeat.destination}</strong>
                    </span>
                    <span class="text-xs text-stone-400">
                      Статус посадки: <span class="font-medium text-stone-300">АСКП • ЕБС</span>
                    </span>
                    <span class="ticket-status-pill {currentSeat.ticketStatus === 'validated' ? 'valid' : 'pending'}">
                      {currentSeat.ticketStatus === 'validated' ? '✓ Посадка подтверждена' : '⏳ Ожидает отметки проводника'}
                    </span>
                  {:else}
                    <span class="text-stone-500 text-xs">Место свободно на всем маршруте</span>
                  {/if}
                </div>
              </div>

              <!-- Правая часть: Кнопка перехода к креслу -->
              <div class="seat-clean-action">
                <button class="action-btn inspect" onclick={handleInspect}>
                  🚶 Подойти к креслу ➔
                </button>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(10, 9, 8, 0.85);
    backdrop-filter: blur(10px);
    padding: 1rem;
  }

  .modal-card {
    position: relative;
    width: 100%;
    max-width: 980px;
    max-height: 92vh;
    display: flex;
    flex-direction: column;
    background: #141210;
    border: 1px solid #2d2924;
    border-radius: 1rem;
    box-shadow:
      0 25px 50px -12px rgba(0, 0, 0, 0.9),
      0 0 30px rgba(245, 158, 11, 0.08);
    overflow: hidden;
  }

  /* Шапка */
  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.1rem 1.5rem;
    background: #1a1816;
    border-bottom: 1px solid #2d2924;
  }

  .train-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #f59e0b;
  }

  .badge-dot {
    width: 6px;
    height: 6px;
    border-radius: 9999px;
    background-color: #f59e0b;
    box-shadow: 0 0 8px #f59e0b;
  }

  .header-title {
    margin-top: 0.15rem;
    font-size: 1.125rem;
    font-weight: 700;
    color: #f5f3ef;
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }

  .class-tag {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.15rem 0.5rem;
    border-radius: 0.375rem;
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.3);
    color: #f59e0b;
  }

  .header-stats {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .stat-pill {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.75rem;
    background: #23201c;
    border: 1px solid #3d3831;
    border-radius: 0.5rem;
    font-size: 0.75rem;
  }

  .stat-pill.alert {
    background: rgba(225, 29, 72, 0.15);
    border-color: rgba(244, 63, 94, 0.5);
  }

  .stat-dot {
    width: 6px;
    height: 6px;
    border-radius: 9999px;
    background-color: #f43f5e;
  }

  .stat-label {
    color: #a8a29e;
  }

  .stat-value {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-weight: 600;
  }

  .close-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 0.5rem;
    background: #23201c;
    border: 1px solid #3d3831;
    color: #a8a29e;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .close-btn:hover {
    background: #332e28;
    color: #f5f3ef;
    border-color: #f59e0b;
  }

  /* Тело модала */
  .modal-body {
    padding: 1.25rem 1.5rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  /* Полоса направления */
  .train-direction-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.4rem 1rem;
    background: #1a1816;
    border: 1px solid #2d2924;
    border-radius: 0.5rem;
    font-size: 0.75rem;
    color: #a8a29e;
  }

  .direction-divider {
    flex-grow: 1;
    height: 1px;
    background: #2d2924;
    margin: 0 1rem;
  }

  .direction-arrow {
    font-size: 0.75rem;
    font-weight: 600;
    color: #f5f3ef;
  }

  /* Сетка схемы */
  .cabin-grid-wrapper {
    background: #0f0e0d;
    border: 1px solid #2d2924;
    border-radius: 0.75rem;
    padding: 1rem 0.75rem;
    overflow-x: auto;
  }

  .cabin-grid {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
    min-width: 780px;
  }

  .grid-row,
  .aisle-row {
    display: grid;
    grid-template-columns: 85px repeat(12, 1fr);
    gap: 0.4rem;
    align-items: center;
  }

  .row-label {
    font-size: 0.6875rem;
    font-weight: 600;
    color: #78716c;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .row-label.aisle-text {
    color: #f59e0b;
  }

  .aisle-marker {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.2rem;
    height: 20px;
    color: #78716c;
    font-family: ui-monospace, SFMono-Regular, monospace;
    font-size: 0.6875rem;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 0.25rem;
  }

  .aisle-num {
    font-weight: 700;
    color: #a8a29e;
  }

  .aisle-arrow {
    color: #f59e0b;
    opacity: 0.6;
  }

  .aisle-marker.row-alert {
    background: rgba(244, 63, 94, 0.22);
    border: 1px solid rgba(244, 63, 94, 0.55);
    box-shadow: 0 0 10px rgba(244, 63, 94, 0.35);
  }

  .aisle-marker.row-alert .aisle-num {
    color: #f43f5e;
  }

  /* Кнопки кресел */
  .seat-btn {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 44px;
    border-radius: 0.375rem;
    background: #1a1816;
    border: 1px solid #2d2924;
    color: #57534e;
    cursor: pointer;
    transition: all 0.15s ease;
    user-select: none;
  }

  .seat-btn:hover {
    border-color: #78716c;
    background: #23201c;
  }

  .seat-btn.occupied {
    background: #201d19;
    border-color: #3d3831;
    color: #d6d3d1;
  }

  .seat-btn.pending {
    border-color: rgba(245, 158, 11, 0.4);
    background: rgba(245, 158, 11, 0.06);
  }

  .seat-btn.validated {
    border-color: rgba(16, 185, 129, 0.4);
    background: rgba(16, 185, 129, 0.08);
  }

  .seat-btn.alert {
    border-color: #f43f5e;
    background: rgba(225, 29, 72, 0.25);
    box-shadow: 0 0 12px rgba(244, 63, 94, 0.4);
    animation: alertPulse 1.8s infinite;
  }

  .seat-btn.row-alert:not(.alert) {
    border-color: rgba(244, 63, 94, 0.45);
    background: rgba(244, 63, 94, 0.08);
  }

  .seat-btn.selected {
    border-color: #f59e0b;
    background: rgba(245, 158, 11, 0.2);
    box-shadow:
      0 0 0 2px #f59e0b,
      0 0 15px rgba(245, 158, 11, 0.4);
    color: #ffffff;
    z-index: 5;
  }

  .seat-id {
    font-family: ui-monospace, SFMono-Regular, monospace;
    font-size: 0.6875rem;
    font-weight: 700;
  }

  .beacon-call {
    font-size: 0.75rem;
    animation: bounce 1.5s infinite;
  }

  .beacon-sick {
    font-size: 0.75rem;
  }

  .beacon-ok {
    font-size: 0.625rem;
    color: #34d399;
    font-weight: bold;
  }

  .beacon-pending {
    font-size: 0.875rem;
    color: #f59e0b;
    line-height: 0.5;
  }

  @keyframes alertPulse {
    0%, 100% {
      border-color: #f43f5e;
    }
    50% {
      border-color: #fda4af;
    }
  }

  @keyframes bounce {
    0%, 100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(-2px);
    }
  }

  /* Легенда */
  .scheme-legend {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 1.25rem;
    padding: 0.5rem 0.5rem;
    font-size: 0.6875rem;
    color: #a8a29e;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .legend-box {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid #3d3831;
    background: #1a1816;
  }

  .legend-box.empty {
    opacity: 0.5;
  }

  .legend-box.pending {
    border-color: #f59e0b;
    background: rgba(245, 158, 11, 0.2);
  }

  .legend-box.validated {
    border-color: #10b981;
    background: rgba(16, 185, 129, 0.25);
  }

  .legend-box.alert {
    border-color: #f43f5e;
    background: rgba(225, 29, 72, 0.4);
  }

  .legend-box.selected {
    border-color: #f59e0b;
    box-shadow: 0 0 0 1px #f59e0b;
    background: #f59e0b;
  }

  /* Детальная карточка пассажира */
  .passenger-card {
    background: #1a1816;
    border: 1px solid #2d2924;
    border-radius: 0.75rem;
    padding: 1.1rem 1.25rem;
  }

  .card-clean-layout {
    display: flex;
    align-items: center;
    gap: 1.25rem;
    padding: 0.25rem 0;
  }

  .seat-clean-info {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    min-width: 0;
  }

  .passenger-name-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .p-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: #f5f3ef;
  }

  .passenger-route-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    font-size: 0.8125rem;
    color: #d6d3d1;
  }

  .route-tag {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
  }

  .ticket-status-pill {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.15rem 0.5rem;
    border-radius: 0.375rem;
  }

  .ticket-status-pill.valid {
    color: #34d399;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.35);
  }

  .ticket-status-pill.pending {
    color: #fbbf24;
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.3);
  }

  .seat-clean-action {
    flex-shrink: 0;
  }

  @media (max-width: 640px) {
    .card-clean-layout {
      flex-direction: column;
      align-items: stretch;
      gap: 0.75rem;
    }
  }

  .action-btn {
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    font-size: 0.8125rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.15s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    white-space: nowrap;
  }

  .action-btn.inspect {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    border: 1px solid #fbbf24;
    color: #0f0e0d;
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.25);
  }

  .action-btn.inspect:hover {
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(245, 158, 11, 0.35);
  }

  .beacon-observe {
    font-size: 0.85rem;
    filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.3));
  }
</style>
