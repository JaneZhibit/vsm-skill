<script lang="ts">
  import { fade, scale } from 'svelte/transition';
  import { authStore } from '../stores/authStore.svelte';
  import { trainWorld } from '../stores/trainWorld.svelte';
  import { conductorState } from '../stores/conductorState.svelte';
  import RadarChart from './RadarChart.svelte';
  import { playClickSound } from '../utils/audio';

  interface Props {
    isOpen: boolean;
    onClose: () => void;
  }

  let { isOpen, onClose }: Props = $props();

  function handleToCabinet() {
    playClickSound();
    onClose();
    trainWorld.abortTrip();
    authStore.setRoute('dashboard');
  }
</script>

{#if isOpen}
  <div class="fixed inset-0 z-[120] bg-black/85 backdrop-blur-md flex items-center justify-center p-4 select-none" transition:fade={{ duration: 200 }}>
    <div class="w-full max-w-lg bg-[#141210] border border-amber-500/50 rounded-2xl p-4 sm:p-6 shadow-2xl flex flex-col gap-4 text-[#f5f3ef]" transition:scale={{ duration: 250, start: 0.95 }}>

      <!-- Шапка -->
      <div class="flex items-center justify-between border-b border-[#2d2924] pb-3">
        <div>
          <span class="text-[9px] font-mono uppercase tracking-wider text-emerald-400 bg-emerald-950/60 border border-emerald-600/40 px-1.5 py-0.5 rounded inline-block mb-1">
            Рейс успешно завершен
          </span>
          <h2 class="text-base sm:text-lg font-bold text-[#f5f3ef] leading-tight">Итоги: Москва ➔ СПб</h2>
          <p class="text-[10px] text-[#a39e95] mt-0.5">Рейс №754 • Поезд «Белый кречет»</p>
        </div>
        <div class="text-right shrink-0 ml-2">
          <div class="text-xl sm:text-2xl font-black font-mono text-amber-400">{conductorState.loyaltyScore} б.</div>
          <div class="text-[9px] text-[#a39e95] uppercase font-mono mt-0.5">Рейтинг</div>
        </div>
      </div>

      <!-- Компактные карточки статистики -->
      <div class="grid grid-cols-2 gap-2 sm:gap-3">
        <div class="p-2.5 rounded-xl bg-[#1a1816] border border-[#2d2924] flex flex-col items-center text-center">
          <span class="text-lg mb-0.5">🤝</span>
          <div class="font-mono font-bold text-amber-400 text-lg leading-none">{conductorState.loyaltyScore}%</div>
          <div class="text-[10px] font-bold text-[#f5f3ef] mt-1">Лояльность</div>
          <div class="text-[8px] text-[#a39e95] leading-tight mt-0.5">Сервис ВСМ</div>
        </div>

        <div class="p-2.5 rounded-xl bg-[#1a1816] border border-[#2d2924] flex flex-col items-center text-center">
          <span class="text-lg mb-0.5">🛡️</span>
          <div class="font-mono font-bold text-emerald-400 text-lg leading-none">{conductorState.safetyScore}%</div>
          <div class="text-[10px] font-bold text-[#f5f3ef] mt-1">Безопасность</div>
          <div class="text-[8px] text-[#a39e95] leading-tight mt-0.5">СТО РЖД</div>
        </div>
      </div>

      <!-- Сжатый график -->
      <div class="bg-[#1a1816] p-2 rounded-xl border border-[#2d2924] flex flex-col items-center overflow-hidden">
        <span class="text-[10px] font-semibold text-[#a39e95] uppercase tracking-wider mb-1">Профиль компетенций ЗУН</span>
        <!-- Отрицательный отступ и scale сжимают график, чтобы он не распирал модальное окно -->
        <div class="w-full flex justify-center scale-[0.80] sm:scale-90 -my-6 sm:-my-4">
          <RadarChart />
        </div>
      </div>

      <!-- Кнопка -->
      <button onclick={handleToCabinet} class="w-full py-3 mt-1 rounded-xl bg-gradient-to-r from-amber-600 via-amber-500 to-yellow-500 hover:from-amber-500 text-stone-950 font-bold text-xs sm:text-sm tracking-wide shadow-lg shadow-amber-500/20 cursor-pointer flex items-center justify-center gap-1.5">
        <span>Перейти в Личный кабинет ➔</span>
      </button>

    </div>
  </div>
{/if}