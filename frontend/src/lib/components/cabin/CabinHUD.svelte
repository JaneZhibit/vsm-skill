<script lang="ts">
  import { fly } from 'svelte/transition';
  import { trainWorld } from '../../stores/trainWorld.svelte';
  import { cabinState } from '../../stores/cabinState.svelte';
  import { physicsState } from '../../stores/trainPhysics.svelte';
  import { conductorState } from '../../stores/conductorState.svelte';

  interface Props {
    onOpenSeatMap: () => void;
  }

  let { onOpenSeatMap }: Props = $props();
</script>

{#if trainWorld.stationToast}
  <div class="station-toast-overlay" transition:fly={{ y: -20, duration: 250 }}>
    <div class="toast-card">
      <div class="toast-title">{trainWorld.stationToast.title}</div>
      <div class="toast-subtitle">{trainWorld.stationToast.subtitle}</div>
    </div>
  </div>
{/if}

<div class="hud-top-bar">
  {#if cabinState.currentView === 'aisle'}
    <div class="aisle-phase-banner">
      {#if conductorState.shiftPhase === 'initial_round'}
        <div class="phase-banner-content phase-round">
          <span class="phase-text">📋 <strong>Приемка вагона (13:50)</strong> • Проверьте оборудование перед рейсом.</span>
        </div>
      {:else if conductorState.shiftPhase === 'cruise'}
        <div class="phase-banner-content phase-cruise">
          <span class="phase-pulse-dot"></span>
          <span class="phase-text">⚡ <strong>В пути ({Math.round(physicsState.speed)} км/ч)</strong></span>
        </div>
      {:else if conductorState.shiftPhase === 'station_warning' || conductorState.shiftPhase === 'tver_warning'}
        <div class="phase-banner-content phase-warning">
          <span class="phase-text">⚠️ <strong>{physicsState.nextStation?.label || 'ст. Тверь'} через 10 мин</strong> • На выход: {cabinState.getNextStationExitingPassengers(physicsState.nextStation?.label || '').length} пасс.</span>
        </div>
      {:else}
        <div class="phase-banner-content phase-arrival">
          <span class="phase-text">🏁 <strong>{physicsState.currentKm >= 679 ? 'Санкт-Петербург Главный' : 'Стоянка на станции'}</strong></span>
        </div>
      {/if}
    </div>

    <div class="top-actions-cluster">
      <button onclick={onOpenSeatMap} class="seat-map-trigger-btn" title="Открыть интерактивную схему мест вагона">
        <span class="trigger-icon">📋</span>
        <span class="trigger-text">Схема ({cabinState.occupiedSeatsCount}/48)</span>
        {#if cabinState.alertSeatsCount > 0}
          <span class="trigger-alert-badge">
            <span class="trigger-alert-ping"></span>
            {cabinState.alertSeatsCount}
          </span>
        {/if}
      </button>
    </div>
  {:else}
    <div class="seat-top-bar">
      <div class="seat-stepper-mini">
        <button onclick={() => cabinState.prevOccupiedSeat()} class="stepper-mini-btn">◀ Пред</button>
        <button onclick={onOpenSeatMap} class="stepper-mini-seat">💺 Место {cabinState.selectedSeat?.id || '—'}</button>
        <button onclick={() => cabinState.nextOccupiedSeat()} class="stepper-mini-btn">След ▶</button>
      </div>
    </div>
  {/if}
</div>

<style>
  .hud-top-bar {
    position: absolute; top: 0.75rem; left: 0.75rem; right: 0.75rem; z-index: 35; display: flex; align-items: center; justify-content: space-between; pointer-events: none;
  }
  .hud-top-bar > * { pointer-events: auto; }
  @media (min-width: 768px) { .hud-top-bar { top: 1.25rem; left: 1.5rem; right: 1.5rem; max-width: 96vw; margin: 0 auto; } }

  .aisle-phase-banner { position: relative; z-index: 25; }
  .phase-banner-content { display: flex; align-items: center; gap: 0.65rem; padding: 0.35rem 0.8rem; border-radius: 0.625rem; background: rgba(20, 18, 16, 0.92); backdrop-filter: blur(10px); border: 1px solid #3d3831; color: #f5f3ef; font-size: 0.75rem; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.6); }
  .phase-round { border-color: rgba(245, 158, 11, 0.4); }
  .phase-cruise { border-color: rgba(59, 130, 246, 0.4); background: rgba(15, 23, 42, 0.92); }
  .phase-warning { border-color: rgba(245, 158, 11, 0.8); background: rgba(45, 30, 15, 0.95); box-shadow: 0 0 20px rgba(245, 158, 11, 0.3); }
  .phase-arrival { border-color: rgba(16, 185, 129, 0.5); background: rgba(10, 30, 20, 0.92); }
  .phase-pulse-dot { width: 8px; height: 8px; border-radius: 50%; background-color: #3b82f6; box-shadow: 0 0 8px #3b82f6; animation: pulse 1.5s infinite; }

  .top-actions-cluster { position: relative; z-index: 25; display: flex; align-items: center; gap: 0.5rem; }
  .seat-map-trigger-btn { display: flex; align-items: center; gap: 0.5rem; padding: 0.45rem 0.85rem; border-radius: 0.625rem; background: rgba(26, 24, 22, 0.9); backdrop-filter: blur(10px); border: 1px solid #3d3831; color: #f5f3ef; font-size: 0.75rem; font-weight: 600; cursor: pointer; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.6); transition: all 0.15s ease; }
  .seat-map-trigger-btn:hover { background: rgba(40, 36, 32, 0.95); border-color: #f59e0b; color: #f59e0b; transform: translateY(-1px); box-shadow: 0 6px 20px rgba(0, 0, 0, 0.7), 0 0 12px rgba(245, 158, 11, 0.2); }
  .trigger-alert-badge { position: relative; display: inline-flex; align-items: center; justify-content: center; padding: 0.1rem 0.4rem; border-radius: 9999px; background: #e11d48; color: #ffffff; font-size: 0.6875rem; font-weight: 700; line-height: 1; }
  .trigger-alert-ping { position: absolute; inset: -2px; border-radius: 9999px; background: #f43f5e; opacity: 0.75; animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite; }

  .seat-top-bar { position: relative; width: 100%; z-index: 25; display: flex; align-items: center; justify-content: center; pointer-events: none; }
  .seat-top-bar > * { pointer-events: auto; }
  .seat-stepper-mini { display: flex; align-items: center; gap: 0.35rem; background: rgba(20, 18, 16, 0.92); backdrop-filter: blur(10px); border: 1px solid #3d3831; padding: 0.25rem 0.4rem; border-radius: 0.625rem; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.6); }
  .stepper-mini-btn { padding: 0.3rem 0.65rem; border-radius: 0.375rem; background: #23201c; border: 1px solid #3d3831; color: #d6d3d1; font-size: 0.75rem; font-weight: 600; cursor: pointer; transition: all 0.15s ease; }
  .stepper-mini-btn:hover { border-color: #f59e0b; color: #f59e0b; background: #2d2822; }
  .stepper-mini-seat { padding: 0.3rem 0.65rem; border-radius: 0.375rem; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); color: #fbbf24; font-family: monospace; font-size: 0.75rem; font-weight: 700; cursor: pointer; }

  .station-toast-overlay { position: absolute; top: 1.25rem; left: 50%; transform: translateX(-50%); z-index: 50; pointer-events: none; max-width: 90vw; }
  .toast-card { display: flex; flex-direction: column; align-items: center; gap: 0.25rem; padding: 0.6rem 1.25rem; border-radius: 0.75rem; background: rgba(20, 18, 16, 0.95); backdrop-filter: blur(14px); border: 1px solid rgba(245, 158, 11, 0.6); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8), 0 0 18px rgba(245, 158, 11, 0.25); text-align: center; color: #f5f3ef; }
  .toast-title { font-size: 0.875rem; font-weight: 700; color: #f59e0b; }
  .toast-subtitle { font-size: 0.75rem; font-weight: 500; color: #d6d3cd; }

  @keyframes ping { 75%, 100% { transform: scale(2); opacity: 0; } }
</style>