<script lang="ts">
  import { trainWorld } from '../../stores/trainWorld.svelte';
  import { cabinState } from '../../stores/cabinState.svelte';
  import { physicsState } from '../../stores/trainPhysics.svelte';
  import { conductorState } from '../../stores/conductorState.svelte';
  import { playClickSound, playSuccessSound } from '../../utils/audio';

  interface Props {
    isTripFinished: boolean;
    onCallClick: (seatId?: string) => void;
    onOpenDebrief: () => void;
  }
  let { isTripFinished, onCallClick, onOpenDebrief }: Props = $props();
</script>

<div class="bottom-ui-panel">
  <div class="pointer-events-auto">
    {#if isTripFinished}
      <button onclick={onOpenDebrief} disabled={!trainWorld.isPostTripDone} class="px-8 py-3 bg-gradient-to-r from-emerald-600 via-emerald-500 to-teal-400 hover:from-emerald-500 text-white font-extrabold rounded-full shadow-[0_0_25px_rgba(16,185,129,0.5)] transition-all hover:scale-105 flex items-center gap-2 cursor-pointer border border-emerald-300 text-sm disabled:opacity-50 disabled:grayscale disabled:hover:scale-100 {trainWorld.isPostTripDone ? 'animate-bounce' : ''}">
        <span>{trainWorld.isPostTripDone ? '🏁 Завершить смену и подвести итоги ➔' : '🧹 Проведите осмотр и уборку вагона...'}</span>
      </button>
    {:else if cabinState.alertSeatsCount > 0}
      {@const incSeat = cabinState.seats.find((s) => s.activeIncident != null)}
      <button onclick={() => onCallClick(incSeat?.id)} class="px-6 py-2.5 bg-gradient-to-r from-rose-600 to-amber-500 text-white font-bold rounded-full shadow-[0_0_20px_rgba(244,63,94,0.6)] animate-pulse flex items-center gap-2 cursor-pointer border border-rose-300">
        <span>🚨 Место {incSeat?.id}: требуется решение проводника ➔</span>
      </button>
    {:else if conductorState.shiftPhase === 'initial_round'}
      <button onclick={() => { playSuccessSound(); trainWorld.startCruisePhase(); }} disabled={!trainWorld.isPreTripDone} class="px-6 py-2.5 bg-gradient-to-r from-amber-600 to-yellow-500 hover:from-amber-500 hover:to-yellow-400 text-stone-950 font-bold rounded-full shadow-[0_4px_20px_rgba(245,158,11,0.4)] transition-all hover:scale-105 flex items-center gap-2 cursor-pointer disabled:opacity-50 disabled:grayscale disabled:hover:scale-100">
        <span>{trainWorld.isPreTripDone ? '🚪 Начать посадку и отправиться ➔' : '🔍 Проведите приемку вагона перед рейсом...'}</span>
      </button>
    {:else if conductorState.shiftPhase === 'cruise'}
      <button onclick={() => { playClickSound(); trainWorld.skipToNextEvent(); }} class="px-6 py-2.5 bg-gradient-to-r from-cyan-600 to-teal-500 hover:from-cyan-500 hover:to-teal-400 text-white font-bold rounded-full shadow-[0_4px_20px_rgba(6,182,212,0.4)] transition-all hover:scale-105 flex items-center gap-2 cursor-pointer">
        <span>⏩ Промотать до события ➔</span>
      </button>
    {:else if conductorState.shiftPhase === 'station_warning' || conductorState.shiftPhase === 'tver_warning'}
      <button onclick={() => { playClickSound(); trainWorld.skipToNextEvent(); }} class="px-6 py-2.5 bg-gradient-to-r from-rose-600 to-orange-500 hover:from-rose-500 hover:to-orange-400 text-white font-bold rounded-full shadow-[0_4px_20px_rgba(225,29,72,0.4)] transition-all hover:scale-105 flex items-center gap-2 cursor-pointer">
        <span>🚉 Перейти к прибытию ➔</span>
      </button>
    {:else if conductorState.shiftPhase === 'arrival'}
      <button onclick={() => { playSuccessSound(); trainWorld.startCruisePhase(); }} class="px-6 py-2.5 bg-gradient-to-r from-amber-600 to-yellow-500 hover:from-amber-500 hover:to-yellow-400 text-stone-950 font-bold rounded-full shadow-[0_4px_20px_rgba(245,158,11,0.4)] transition-all hover:scale-105 flex items-center gap-2 cursor-pointer">
        <span>⏩ Отправление дальше ➔</span>
      </button>
    {/if}
  </div>

  <div class="pointer-events-auto w-full bg-[#141210]/95 backdrop-blur-md border border-[#3d3831] rounded-2xl p-3 sm:p-4 shadow-2xl flex flex-col gap-2">
    <div class="flex justify-between items-center text-[11px] font-mono text-[#a39e95] uppercase font-semibold">
      <span class="text-[#f5f3ef] bg-[#282420] px-2 py-0.5 rounded border border-[#3d3831]">🕒 {physicsState.formattedTime}</span>
      <div class="text-center flex flex-col items-center">
        <span class="text-amber-400 text-xs">След: {physicsState.nextStation?.label || 'Санкт-Петербург Главный'}</span>
        <span class="text-[10px] opacity-70">Прибытие: {physicsState.nextStation?.plannedTime || '16:15'}</span>
      </div>
      <span>С-Петербург (16:15)</span>
    </div>
    <div class="relative w-full h-1.5 bg-[#2d2924] rounded-full mt-1">
      <div class="absolute top-0 left-0 h-full bg-amber-500 rounded-full transition-all duration-1000 ease-out" style="width: {physicsState.progressPercent}%"></div>
      <div class="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-amber-500 rounded-full shadow-[0_0_10px_rgba(245,158,11,0.8)] transition-all duration-1000 ease-out" style="left: {physicsState.progressPercent}%"></div>
    </div>
  </div>
</div>

<style>
  .bottom-ui-panel { position: absolute; bottom: 1.5rem; left: 50%; transform: translateX(-50%); width: 91.666667%; max-width: 48rem; z-index: 30; display: flex; flex-direction: column; align-items: center; gap: 1rem; pointer-events: none; }
  @media (max-width: 767px) { .bottom-ui-panel { position: relative; bottom: auto; left: auto; transform: none; width: 100%; max-width: none; flex-shrink: 0; z-index: 30; padding: 0.75rem 1rem 1rem; background: #0f0e0d; border-top: 1px solid #262320; border-radius: 1rem; margin-top: 0.5rem; pointer-events: auto; } }
</style>