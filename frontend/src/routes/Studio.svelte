<script lang="ts">
  import { playClickSound, playSuccessSound, playErrorSound } from '../lib/utils/audio';

  let activeTab = $state<'cases' | 'handbook' | 'constructor'>('cases');

  // Поля формы No-Code конструктора сценариев
  let customTitle = $state<string>('Пассажир громко слушает музыку без наушников');
  let customPrompt = $state<string>('«А что такого? Я в своем купе... то есть кресле, трек классный! Наденьте беруши, если не нравится!»');
  let customTimer = $state<number>(15);

  let opt1Text = $state<string>('Вежливо сослаться на п. 4.12 СТО РЖД о звуковом комфорте и предложить фирменные наушники ВСМ.');
  let opt1Feedback = $state<string>('Идеально (СТО РЖД 03.011). Предотвратили конфликт между пассажирами и предложили премиальный сервис.');
  let opt1Loyalty = $state<number>(15);
  let opt1Safety = $state<number>(10);

  let opt2Text = $state<string>('Выдернуть телефон из рук или пригрозить вызовом наряда полиции.');
  let opt2Feedback = $state<string>('Грубое нарушение корпоративного стандарта РЖД. Эскалация конфликта и превышение полномочий.');
  let opt2Loyalty = $state<number>(-30);
  let opt2Safety = $state<number>(-15);

  let isSaving = $state<boolean>(false);
  let successMessage = $state<string | null>(null);
  let errorMessage = $state<string | null>(null);

  async function handleSaveScenario() {
    playClickSound();
    isSaving = true;
    successMessage = null;
    errorMessage = null;

    const payload = {
      incident_id: `custom_inc_${Date.now()}`,
      title: customTitle.trim() || 'Пользовательский инцидент',
      prompt: customPrompt.trim() || 'Обращение пассажира',
      timer_seconds: Number(customTimer) || 15,
      opt_1_text: opt1Text.trim(),
      opt_1_feedback: opt1Feedback.trim(),
      opt_1_loyalty: Number(opt1Loyalty) || 15,
      opt_1_safety: Number(opt1Safety) || 10,
      opt_2_text: opt2Text.trim(),
      opt_2_feedback: opt2Feedback.trim(),
      opt_2_loyalty: Number(opt2Loyalty) || -20,
      opt_2_safety: Number(opt2Safety) || -10,
    };

    try {
      const res = await fetch('/api/v1/simulation/custom-scenario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        playSuccessSound();
        successMessage = 'Сценарий успешно добавлен в базу и готов к проверке в симуляторе!';
      } else {
        throw new Error(`Ошибка сервера: ${res.status}`);
      }
    } catch (err: any) {
      playErrorSound();
      errorMessage = err?.message || 'Не удалось сохранить сценарий';
    } finally {
      isSaving = false;
    }
  }
</script>

<div class="w-full max-w-5xl mx-auto p-4 sm:p-6 flex flex-col gap-6">
  <header class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#2d2924] pb-4">
    <div>
      <h1 class="text-lg sm:text-xl font-bold text-[#f5f3ef] tracking-wide">Студия регламентов и разборов</h1>
      <p class="text-xs text-[#a39e95] mt-0.5">База знаний СТО РЖД 2026 и No-Code конструктор новых сценариев</p>
    </div>
    <div class="bg-[#1a1816] p-1 rounded-xl border border-[#2d2924] inline-flex gap-1 flex-wrap">
      <button
        onclick={() => { activeTab = 'cases'; playClickSound(); }}
        class="px-3.5 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-all {activeTab === 'cases' ? 'bg-[#282420] text-amber-300 border border-[#3d3831] shadow-sm' : 'text-[#a39e95]'}"
      >
        Разбор ошибок
      </button>
      <button
        onclick={() => { activeTab = 'handbook'; playClickSound(); }}
        class="px-3.5 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-all {activeTab === 'handbook' ? 'bg-[#282420] text-amber-300 border border-[#3d3831] shadow-sm' : 'text-[#a39e95]'}"
      >
        Стандарты СТО РЖД
      </button>
      <button
        onclick={() => { activeTab = 'constructor'; playClickSound(); }}
        class="px-3.5 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-all {activeTab === 'constructor' ? 'bg-amber-950/40 text-amber-300 border border-amber-500/60 shadow-sm' : 'text-[#a39e95]'}"
      >
        ✍️ Конструктор инцидентов
      </button>
    </div>
  </header>

  {#if activeTab === 'cases'}
    <div class="space-y-3">
      <div class="p-4 rounded-xl bg-[#1a1816] border border-[#2d2924] flex flex-col gap-2">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-amber-400">Кейс № 28: Запрос личных медикаментов</span>
          <span class="text-[10px] text-rose-400 font-mono font-semibold">Частая ошибка</span>
        </div>
        <p class="text-xs text-[#a39e95] leading-relaxed">
          Проводник выдал пассажиру собственный обезболивающий препарат. Пассажир получил аллергическую реакцию.
          <strong class="text-[#f5f3ef]">Правило:</strong> выдача личных лекарств категорически запрещена. Только аптечка первой помощи или вызов медика по громкой связи.
        </p>
      </div>

      <div class="p-4 rounded-xl bg-[#1a1816] border border-[#2d2924] flex flex-col gap-2">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-amber-400">Кейс № 6: Неадекватный пассажир</span>
          <span class="text-[10px] text-emerald-400 font-mono font-semibold">Стандарт безопасности</span>
        </div>
        <p class="text-xs text-[#a39e95] leading-relaxed">
          При вызове начальника поезда по служебной радиосвязи запрещено произносить слово «пьяный», чтобы не спровоцировать пассажира на агрессию.
        </p>
      </div>
    </div>
  {:else if activeTab === 'handbook'}
    <div class="p-5 rounded-2xl bg-[#1a1816] border border-[#2d2924] space-y-3 text-xs leading-relaxed text-[#a39e95]">
      <h3 class="font-bold text-[#f5f3ef]">СТО РЖД 03.011–2026: Нормативы комфорта вагона 1-го класса</h3>
      <ul class="list-disc pl-5 space-y-1">
        <li>Температурный режим: 20–24°C при внешней температуре до 10°C; 24–28°C в жару.</li>
        <li>Время ожидания обслуживания: в первом классе не более 5 минут, в бизнес-классе не более 10 минут.</li>
        <li>За 15 минут до прибытия на конечную станцию завершаются все платные сервисы и торговля.</li>
      </ul>
    </div>
  {:else if activeTab === 'constructor'}
    <!-- Конструктор инцидентов для демонстрации жюри (Критерий 2) -->
    <div class="p-5 rounded-2xl bg-[#1a1816] border border-[#2d2924] flex flex-col gap-5">
      <div class="flex items-center justify-between border-b border-[#2d2924] pb-3">
        <div>
          <h2 class="text-sm font-bold text-[#f5f3ef] tracking-wide flex items-center gap-2">
            <span>🛠️ Интерактивный No-Code редактор сценариев</span>
            <span class="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 font-mono">ЖИВОЙ РЕЕСТР</span>
          </h2>
          <p class="text-xs text-[#a39e95] mt-0.5">Создайте инцидент прямо сейчас без изменения кода ядра симулятора</p>
        </div>
      </div>

      {#if successMessage}
        <div class="p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 text-xs flex items-center gap-2.5">
          <span class="text-base">✅</span>
          <span>{successMessage}</span>
        </div>
      {/if}

      {#if errorMessage}
        <div class="p-3.5 rounded-xl bg-rose-950/60 border border-rose-500/50 text-rose-300 text-xs flex items-center gap-2.5">
          <span class="text-base">❌</span>
          <span>{errorMessage}</span>
        </div>
      {/if}

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Название и таймер -->
        <div class="md:col-span-2 space-y-1.5">
          <label for="scenario-title" class="text-xs text-[#a39e95] font-semibold">Название ситуации (Кратко)</label>
          <input
            id="scenario-title"
            bind:value={customTitle}
            type="text"
            class="w-full px-3.5 py-2 rounded-xl bg-[#141210] border border-[#2d2924] focus:border-amber-400 text-xs text-[#f5f3ef] outline-none"
            placeholder="Например: Пассажир уронил ноутбук в проход"
          />
        </div>

        <div class="space-y-1.5">
          <label for="scenario-timer" class="text-xs text-[#a39e95] font-semibold">Лимит времени (сек)</label>
          <input
            id="scenario-timer"
            bind:value={customTimer}
            type="number"
            min="5"
            max="60"
            class="w-full px-3.5 py-2 rounded-xl bg-[#141210] border border-[#2d2924] focus:border-amber-400 text-xs text-[#f5f3ef] font-mono outline-none"
          />
        </div>

        <!-- Реплика пассажира -->
        <div class="md:col-span-3 space-y-1.5">
          <label for="scenario-prompt" class="text-xs text-[#a39e95] font-semibold">Прямая речь пассажира (Текст Typewriter)</label>
          <textarea
            id="scenario-prompt"
            bind:value={customPrompt}
            rows="2"
            class="w-full px-3.5 py-2 rounded-xl bg-[#141210] border border-[#2d2924] focus:border-amber-400 text-xs text-[#f5f3ef] outline-none"
            placeholder="«Проводник, помогите...»"
          ></textarea>
        </div>
      </div>

      <!-- Варианты ответов -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-[#2d2924]">
        <!-- Вариант 1 (Верный) -->
        <div class="p-4 rounded-xl bg-[#141210] border border-emerald-900/40 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
              <span>🟢</span> Вариант 1: Корректное действие
            </span>
          </div>
          <div class="space-y-1">
            <label for="opt1-text" class="text-[11px] text-[#a39e95]">Текст кнопки проводника</label>
            <input
              id="opt1-text"
              bind:value={opt1Text}
              type="text"
              class="w-full px-3 py-1.5 rounded-lg bg-[#1a1816] border border-[#2d2924] text-xs text-[#f5f3ef] outline-none"
            />
          </div>
          <div class="space-y-1">
            <label for="opt1-feedback" class="text-[11px] text-[#a39e95]">Обоснование по СТО РЖД</label>
            <input
              id="opt1-feedback"
              bind:value={opt1Feedback}
              type="text"
              class="w-full px-3 py-1.5 rounded-lg bg-[#1a1816] border border-[#2d2924] text-xs text-[#f5f3ef] outline-none"
            />
          </div>
          <div class="grid grid-cols-2 gap-2 text-xs">
            <div>
              <label for="opt1-loyalty" class="text-[10px] text-[#a39e95]">Δ Лояльность</label>
              <input id="opt1-loyalty" bind:value={opt1Loyalty} type="number" class="w-full px-2 py-1 rounded bg-[#1a1816] border border-[#2d2924] text-xs font-mono text-amber-300" />
            </div>
            <div>
              <label for="opt1-safety" class="text-[10px] text-[#a39e95]">Δ Безопасность</label>
              <input id="opt1-safety" bind:value={opt1Safety} type="number" class="w-full px-2 py-1 rounded bg-[#1a1816] border border-[#2d2924] text-xs font-mono text-emerald-300" />
            </div>
          </div>
        </div>

        <!-- Вариант 2 (Ошибочный) -->
        <div class="p-4 rounded-xl bg-[#141210] border border-rose-900/40 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-rose-400 flex items-center gap-1.5">
              <span>🔴</span> Вариант 2: Ошибочное действие
            </span>
          </div>
          <div class="space-y-1">
            <label for="opt2-text" class="text-[11px] text-[#a39e95]">Текст кнопки проводника</label>
            <input
              id="opt2-text"
              bind:value={opt2Text}
              type="text"
              class="w-full px-3 py-1.5 rounded-lg bg-[#1a1816] border border-[#2d2924] text-xs text-[#f5f3ef] outline-none"
            />
          </div>
          <div class="space-y-1">
            <label for="opt2-feedback" class="text-[11px] text-[#a39e95]">Разбор ошибки</label>
            <input
              id="opt2-feedback"
              bind:value={opt2Feedback}
              type="text"
              class="w-full px-3 py-1.5 rounded-lg bg-[#1a1816] border border-[#2d2924] text-xs text-[#f5f3ef] outline-none"
            />
          </div>
          <div class="grid grid-cols-2 gap-2 text-xs">
            <div>
              <label for="opt2-loyalty" class="text-[10px] text-[#a39e95]">Δ Лояльность</label>
              <input id="opt2-loyalty" bind:value={opt2Loyalty} type="number" class="w-full px-2 py-1 rounded bg-[#1a1816] border border-[#2d2924] text-xs font-mono text-rose-300" />
            </div>
            <div>
              <label for="opt2-safety" class="text-[10px] text-[#a39e95]">Δ Безопасность</label>
              <input id="opt2-safety" bind:value={opt2Safety} type="number" class="w-full px-2 py-1 rounded bg-[#1a1816] border border-[#2d2924] text-xs font-mono text-rose-300" />
            </div>
          </div>
        </div>
      </div>

      <div class="flex justify-end pt-3 border-t border-[#2d2924]">
        <button
          onclick={handleSaveScenario}
          disabled={isSaving}
          class="px-6 py-3 rounded-xl bg-gradient-to-r from-amber-600 via-amber-500 to-yellow-500 hover:from-amber-500 text-stone-950 font-bold text-xs sm:text-sm tracking-wide shadow-lg shadow-amber-500/20 cursor-pointer transition-all flex items-center gap-2"
        >
          <span>{isSaving ? '⏳ Сохранение...' : '🚀 Сохранить в реестр ВСМ'}</span>
        </button>
      </div>
    </div>
  {/if}
</div>
