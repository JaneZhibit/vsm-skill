<script lang="ts">
  import { fade, scale } from 'svelte/transition';
  import { authStore } from '../stores/authStore.svelte';
  import { trainWorld } from '../stores/trainWorld.svelte';
  import RadarChart from './RadarChart.svelte';
  import { playSuccessSound, playClickSound } from '../utils/audio';

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
    <div class="w-full max-w-2xl bg-[#141210] border border-amber-500/50 rounded-3xl p-6 shadow-2xl flex flex-col gap-5 text-[#f5f3ef]" transition:scale={{ duration: 250, start: 0.95 }}>
      <!-- Заголовок -->
      <div class="flex items-center justify-between border-b border-[#2d2924] pb-4">
        <div>
          <span class="text-[10px] font-mono uppercase tracking-wider text-emerald-400 bg-emerald-950/60 border border-emerald-600/40 px-2 py-0.5 rounded">
            Рейс № 754 успешно завершен
          </span>
          <h2 class="text-xl font-bold text-[#f5f3ef] mt-1">Итоги смены: Москва ➔ Санкт-Петербург</h2>
          <p class="text-xs text-[#a39e95]">Пройдено 679 км • 16 станций • Поезд «Белый кречет»</p>
        </div>
        <div class="text-right">
          <div class="text-2xl font-black font-mono text-amber-400">{trainWorld.loyaltyScore} б.</div>
          <div class="text-[10px] text-[#a39e95] uppercase font-mono">Итоговый рейтинг</div>
        </div>
      </div>

      <!-- Две параллельные шкалы (Требование ТЗ!) -->
      <div class="grid grid-cols-2 gap-3">
        <div class="p-3.5 rounded-2xl bg-[#1a1816] border border-[#2d2924] flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <span class="text-xl">🤝</span>
            <div>
              <div class="text-xs font-bold text-[#f5f3ef]">Лояльность пассажиров</div>
              <div class="text-[10px] text-[#a39e95]">Сервисный стандарт ВСМ</div>
            </div>
          </div>
          <div class="font-mono font-bold text-amber-400 text-base">{trainWorld.loyaltyScore}%</div>
        </div>

        <div class="p-3.5 rounded-2xl bg-[#1a1816] border border-[#2d2924] flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <span class="text-xl">🛡️</span>
            <div>
              <div class="text-xs font-bold text-[#f5f3ef]">Рейтинг безопасности</div>
              <div class="text-[10px] text-[#a39e95]">Регламенты СТО РЖД</div>
            </div>
          </div>
          <div class="font-mono font-bold text-emerald-400 text-base">{trainWorld.safetyScore}%</div>
        </div>
      </div>

      <!-- Радарная диаграмма ЗУН -->
      <div class="bg-[#1a1816] p-4 rounded-2xl border border-[#2d2924] flex flex-col items-center">
        <span class="text-[11px] font-semibold text-[#a39e95] uppercase tracking-wider mb-1">
          Обновленный профиль компетенций ЗУН
        </span>
        <div class="w-full flex justify-center scale-90 -my-2">
          <RadarChart />
        </div>
      </div>

      <!-- Кнопки завершения -->
      <div class="flex items-center justify-end gap-3 pt-2 border-t border-[#2d2924]">
        <button
          onclick={handleToCabinet}
          class="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-amber-600 via-amber-500 to-yellow-500 hover:from-amber-500 text-stone-950 font-bold text-xs sm:text-sm tracking-wide shadow-lg shadow-amber-500/20 cursor-pointer flex items-center justify-center gap-2"
        >
          <span>Перейти в Личный кабинет и рейтинг ➔</span>
        </button>
      </div>
    </div>
  </div>
{/if}
