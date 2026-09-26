<script lang="ts">
  import { fade, scale } from 'svelte/transition';
  import { playClickSound } from '../utils/audio';

  interface Props {
    isOpen: boolean;
    onClose: () => void;
    report: any;
  }

  let { isOpen, onClose, report }: Props = $props();

  function handleClose() {
    playClickSound();
    onClose();
  }

  function handlePrint() {
    if (typeof window !== 'undefined') {
      window.print();
    }
  }
</script>

{#if isOpen && report}
  <div
    class="fixed inset-0 z-[130] bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-5 select-none"
    transition:fade={{ duration: 200 }}
  >
    <div
      class="w-full max-w-3xl bg-[#141210] border border-amber-500/50 rounded-3xl p-5 sm:p-7 shadow-2xl flex flex-col gap-5 text-[#f5f3ef] max-h-[90vh] overflow-y-auto"
      transition:scale={{ duration: 250, start: 0.95 }}
    >
      <!-- Шапка официального документа -->
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#2d2924] pb-4">
        <div class="flex items-center gap-3">
          <div class="w-11 h-11 rounded-xl bg-gradient-to-tr from-amber-600 via-amber-500 to-yellow-500 flex items-center justify-center text-xl text-stone-950 font-black shadow-md shadow-amber-500/20">
            ВСМ
          </div>
          <div>
            <div class="text-[10px] text-amber-400 font-mono uppercase tracking-wider font-bold">
              ОАО «РЖД» • Департамент пассажирских сообщений
            </div>
            <h2 class="text-base sm:text-lg font-bold text-[#f5f3ef]">
              Квалификационный профиль сотрудника (LMS/HR)
            </h2>
            <div class="text-[11px] text-[#a39e95]">
              Интеграционный шлюз ЕКАСУТР • ID: {report.employee.id}
            </div>
          </div>
        </div>
        <div class="text-right shrink-0">
          <span class="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-950/60 border border-emerald-500/40 text-emerald-300">
            {report.qualification.status}
          </span>
          <div class="text-[10px] text-[#706b63] font-mono mt-1">
            Дата выгрузки: {new Date(report.generated_at).toLocaleString('ru-RU')}
          </div>
        </div>
      </div>

      <!-- Карточка сотрудника и индекс готовности -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        <div class="p-4 rounded-2xl bg-[#1a1816] border border-[#2d2924] md:col-span-2 flex flex-col justify-between">
          <div class="space-y-1">
            <span class="text-[10px] font-mono text-[#a39e95] uppercase">Сотрудник поездной бригады</span>
            <div class="text-base font-bold text-[#f5f3ef]">{report.employee.full_name}</div>
            <div class="text-xs text-amber-300/90 font-mono">{report.employee.role} • {report.employee.badge}</div>
          </div>
          <div class="pt-3 border-t border-[#2d2924] mt-3 flex items-center justify-between text-xs text-[#a39e95]">
            <span>Завершено смен по графику:</span>
            <span class="font-bold text-[#f5f3ef] font-mono">{report.employee.shifts_completed}</span>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-[#1a1816] border border-[#2d2924] flex flex-col justify-between items-center text-center">
          <span class="text-[10px] font-mono text-[#a39e95] uppercase">Индекс ЗУН (Общий)</span>
          <div class="text-4xl font-black font-mono text-amber-400 my-1">
            {report.qualification.overall_index}%
          </div>
          <span class="text-[11px] text-emerald-400 font-semibold">
            Безопасность: {report.qualification.safety_rating}%
          </span>
        </div>
      </div>

      <!-- Матрица 4 ключевых компетенций -->
      <div class="p-4 rounded-2xl bg-[#1a1816] border border-[#2d2924] space-y-3">
        <div class="text-xs font-bold text-[#f5f3ef] uppercase tracking-wider flex items-center justify-between">
          <span>Оценка векторов профессионального стандарта СТО РЖД</span>
          <span class="text-[10px] text-[#a39e95] font-normal font-mono">Шкала 0–100%</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          {#each Object.entries(report.competencies_matrix) as [name, val]}
            <div class="p-2.5 rounded-xl bg-[#141210] border border-[#282420] flex flex-col gap-1.5">
              <div class="flex items-center justify-between text-xs">
                <span class="text-[#d6d3d1]">{name}</span>
                <span class="font-mono font-bold text-amber-400">{val}%</span>
              </div>
              <div class="h-1.5 w-full bg-[#282420] rounded-full overflow-hidden">
                <div class="h-full bg-gradient-to-r from-amber-600 to-amber-400 rounded-full" style="width: {val}%;"></div>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <!-- Рекомендация для HR / Руководителя -->
      <div class="p-4 rounded-2xl bg-amber-950/20 border border-amber-600/40 space-y-1.5">
        <div class="flex items-center gap-2 text-xs font-bold text-amber-300 uppercase tracking-wide">
          <span>📋</span>
          <span>План индивидуального развития (LMS автоматизация)</span>
        </div>
        <p class="text-xs text-[#a39e95] leading-relaxed">
          {report.recommendation.action_plan}. Выявлена потребность в закреплении практических кейсов по направлению
          <strong class="text-amber-200">«{report.recommendation.weak_area}»</strong> (текущий показатель: {report.recommendation.score}%).
        </p>
      </div>

      <!-- Кнопки действий -->
      <div class="flex items-center justify-between pt-3 border-t border-[#2d2924] gap-3">
        <button
          onclick={handlePrint}
          class="px-4 py-2.5 rounded-xl bg-[#282420] hover:bg-[#342f2a] border border-[#3d3831] text-xs text-[#f5f3ef] font-semibold cursor-pointer transition-all flex items-center gap-1.5"
        >
          <span>🖨️</span> <span>Печать профиля</span>
        </button>

        <button
          onclick={handleClose}
          class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-600 via-amber-500 to-yellow-500 hover:from-amber-500 text-stone-950 font-bold text-xs cursor-pointer shadow-md transition-all"
        >
          Закрыть
        </button>
      </div>
    </div>
  </div>
{/if}
