<script lang="ts">
  import { playClickSound, playSuccessSound, playErrorSound } from '../lib/utils/audio';

  let activeTab = $state<'cases' | 'handbook' | 'constructor'>('constructor');

  // Данные конструктора
  let customTitle = $state<string>('');
  let targetArchetype = $state<string>('any');
  
  // Триггеры
  let triggerType = $state<'time' | 'speed' | 'random' | 'chained'>('time');
  let triggerValue = $state<number>(15);
  let triggerParentId = $state<string>('');
  let triggerDelay = $state<number>(40);

  // Категории навыков (Мультиселект)
  let skills = $state({ safety: false, service: true, medicine: false, discipline: false });

  // Поведение
  let passengerState = $state<string>('annoyed');
  let isPassive = $state<boolean>(true);
  let llmSystemPrompt = $state<string>('');
  let expectedRule = $state<string>('');

  let isSaving = $state<boolean>(false);
  let successMessage = $state<string | null>(null);
  let errorMessage = $state<string | null>(null);
  let lastCreatedId = $state<string | null>(null);
  let copyFeedback = $state<boolean>(false);

  async function handleSaveScenario() {
    playClickSound();
    isSaving = true;
    successMessage = null;
    errorMessage = null;

    // Собираем выбранные скиллы в массив
    const selectedSkills = Object.entries(skills)
      .filter(([_, isSelected]) => isSelected)
      .map(([key]) => key);

    const generatedIncidentId = customTitle.trim() ? `live_evt_${customTitle.trim().toLowerCase().replace(/\s+/g, '_')}_${Date.now()}` : `live_evt_${Date.now()}`;
    const payload = {
      incident_id: generatedIncidentId,
      title: customTitle.trim() || 'Новое событие',
      target_archetype: targetArchetype,
      trigger: {
        type: triggerType,
        value: triggerType !== 'chained' ? Number(triggerValue) : null,
        parent_id: triggerType === 'chained' ? triggerParentId.trim() : null,
        delay_sec: triggerType === 'chained' ? Number(triggerDelay) : null
      },
      passenger_state: passengerState,
      is_passive: isPassive,
      llm_system_prompt: llmSystemPrompt.trim(),
      expected_rule: expectedRule.trim(),
      skills: selectedSkills
    };

    try {
      const res = await fetch('/api/v1/simulation/custom-live-scenario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();
        const createdId = data.incident_id || generatedIncidentId;
        lastCreatedId = createdId;
        playSuccessSound();
        successMessage = `Событие успешно зарегистрировано в GameMaster! ID: ${createdId}`;
        customTitle = '';
      } else {
        throw new Error(`Ошибка: ${res.status}`);
      }
    } catch (err: any) {
      playErrorSound();
      errorMessage = err?.message || 'Не удалось сохранить';
    } finally {
      isSaving = false;
    }
  }

  function useAsChainedParent() {
    if (lastCreatedId) {
      triggerType = 'chained';
      triggerParentId = lastCreatedId;
      playClickSound();
    }
  }

  async function copyLastId() {
    if (lastCreatedId) {
      await navigator.clipboard.writeText(lastCreatedId);
      copyFeedback = true;
      setTimeout(() => { copyFeedback = false; }, 2000);
      playClickSound();
    }
  }
</script>

<div class="w-full max-w-5xl mx-auto p-4 sm:p-6 flex flex-col gap-6">
  <header class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#2d2924] pb-4">
    <div>
      <h1 class="text-lg sm:text-xl font-bold text-[#f5f3ef] tracking-wide">Студия сценариев</h1>
      <p class="text-xs text-[#a39e95] mt-0.5">Создание эмерджентных (живых) ситуаций для PRO-симуляции</p>
    </div>
    <div class="bg-[#1a1816] p-1 rounded-xl border border-[#2d2924] inline-flex gap-1">
      <button onclick={() => { activeTab = 'constructor'; playClickSound(); }} class="px-3.5 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-all {activeTab === 'constructor' ? 'bg-amber-950/40 text-amber-300 border border-amber-500/60 shadow-sm' : 'text-[#a39e95]'}">
        ⚙️ Event-Конструктор
      </button>
      <button onclick={() => { activeTab = 'handbook'; playClickSound(); }} class="px-3.5 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-all {activeTab === 'handbook' ? 'bg-[#282420] text-amber-300 border border-[#3d3831] shadow-sm' : 'text-[#a39e95]'}">
        База знаний
      </button>
    </div>
  </header>

  {#if activeTab === 'constructor'}
    <div class="p-5 rounded-2xl bg-[#141210] border border-[#2d2924] flex flex-col gap-6 shadow-xl">
      <div class="flex items-center justify-between border-b border-[#2d2924] pb-3">
        <div>
          <h2 class="text-base font-bold text-amber-400 flex items-center gap-2">
            <span>⚙️ Event-Конструктор (Движок PRO-режима)</span>
          </h2>
          <p class="text-[11px] text-[#a39e95] mt-1">Определите условия, связи графа и развиваемые компетенции.</p>
        </div>
      </div>

      {#if successMessage}
        <div class="p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <span class="flex items-center gap-2">✅ {successMessage}</span>
          <div class="flex items-center gap-2">
            <button onclick={copyLastId} class="px-2.5 py-1 bg-emerald-900/60 hover:bg-emerald-800 text-[11px] rounded border border-emerald-400/40 cursor-pointer transition-all font-mono">
              {copyFeedback ? '✓ Скопировано' : '📋 Скопировать ID'}
            </button>
            <button onclick={useAsChainedParent} class="px-2.5 py-1 bg-indigo-900/60 hover:bg-indigo-800 text-[11px] rounded border border-indigo-400/40 cursor-pointer transition-all text-indigo-200">
              🔗 Связать следующее событие
            </button>
          </div>
        </div>
      {/if}
      {#if errorMessage}
        <div class="p-3.5 rounded-xl bg-rose-950/60 border border-rose-500/50 text-rose-300 text-xs flex items-center gap-2.5">❌ {errorMessage}</div>
      {/if}

      <!-- БЛОК: ТЕГИ КОМПЕТЕНЦИЙ -->
      <div class="p-3.5 rounded-xl bg-[#1a1816] border border-[#3d3831]">
        <label for="competence-group" class="text-[11px] font-bold text-stone-300 uppercase tracking-wider block mb-2">Категории развития (Для ИИ-подбора в PRO)</label>
        <div id="competence-group" class="flex flex-wrap gap-2">
          <label class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border cursor-pointer transition-all {skills.service ? 'bg-amber-950/40 border-amber-500 text-amber-300' : 'bg-[#0f0e0d] border-[#3d3831] text-[#706b63]'}">
            <input type="checkbox" bind:checked={skills.service} class="hidden" /> 🤝 Сервис
          </label>
          <label class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border cursor-pointer transition-all {skills.safety ? 'bg-emerald-950/40 border-emerald-500 text-emerald-300' : 'bg-[#0f0e0d] border-[#3d3831] text-[#706b63]'}">
            <input type="checkbox" bind:checked={skills.safety} class="hidden" /> 🛡️ Безопасность
          </label>
          <label class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border cursor-pointer transition-all {skills.medicine ? 'bg-rose-950/40 border-rose-500 text-rose-300' : 'bg-[#0f0e0d] border-[#3d3831] text-[#706b63]'}">
            <input type="checkbox" bind:checked={skills.medicine} class="hidden" /> 🩺 Медицина
          </label>
          <label class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border cursor-pointer transition-all {skills.discipline ? 'bg-blue-950/40 border-blue-500 text-blue-300' : 'bg-[#0f0e0d] border-[#3d3831] text-[#706b63]'}">
            <input type="checkbox" bind:checked={skills.discipline} class="hidden" /> 📜 Регламент
          </label>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        <!-- ЛЕВАЯ КОЛОНКА: БАЗА И ТРИГГЕРЫ -->
        <div class="space-y-4">
          <!-- КТО -->
          <div class="p-4 rounded-xl bg-[#1a1816] border border-[#3d3831] space-y-3">
            <h3 class="text-xs font-bold text-stone-300 uppercase tracking-wider mb-2 border-b border-[#2d2924] pb-1">1. Идентификация</h3>
            
            <div class="space-y-1.5">
              <label for="custom-title-input" class="text-[11px] text-[#a39e95]">Название события (для логов)</label>
              <input id="custom-title-input" bind:value={customTitle} type="text" class="w-full px-3 py-2 rounded-lg bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-white outline-none" placeholder="Например: Плачущий ребенок" />
            </div>

            <div class="space-y-1.5">
              <label for="target-archetype-select" class="text-[11px] text-[#a39e95]">Архетип пассажира</label>
              <select id="target-archetype-select" bind:value={targetArchetype} class="w-full px-3 py-2 rounded-lg bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-white outline-none">
                <option value="any">🎲 Любой (Случайный)</option>
                <option value="male_young">👨 Молодой мужчина</option>
                <option value="female_young">👩 Молодая девушка</option>
                <option value="female_elderly">👵 Пожилая женщина</option>
              </select>
            </div>
          </div>

          <!-- КОГДА (Динамический триггер) -->
          <div class="p-4 rounded-xl bg-[#1a1816] border border-[#3d3831] space-y-3 relative overflow-hidden">
            <h3 class="text-xs font-bold text-stone-300 uppercase tracking-wider mb-2 border-b border-[#2d2924] pb-1">2. Условия срабатывания</h3>
            
            <div class="space-y-1.5">
              <label for="trigger-type-select" class="text-[11px] text-[#a39e95]">Тип триггера</label>
              <select id="trigger-type-select" bind:value={triggerType} class="w-full px-3 py-2 rounded-lg bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs font-bold text-amber-300 outline-none">
                <option value="time">⏱ По таймеру (Через X сек после старта)</option>
                <option value="speed">🚄 По скорости (Свыше X км/ч)</option>
                <option value="random">🎲 Случайное (X% шанс)</option>
                <option value="chained">🔗 Цепная реакция (Эффект бабочки)</option>
              </select>
            </div>

            <!-- Динамическое поле в зависимости от типа триггера -->
            {#if triggerType === 'chained'}
              <div class="p-3 rounded-lg bg-indigo-950/20 border border-indigo-500/30 space-y-3">
                <div class="space-y-1.5">
                  <label for="trigger-parent-input" class="text-[11px] text-indigo-300 font-mono">ID родительского события</label>
                  <input id="trigger-parent-input" bind:value={triggerParentId} type="text" class="w-full px-3 py-1.5 rounded bg-[#0f0e0d] border border-[#3d3831] text-xs text-white" placeholder="Например: live_crying_child" />
                </div>
                <div class="space-y-1.5">
                  <label for="trigger-delay-input" class="text-[11px] text-indigo-300 font-mono">Активировать если не решено (сек):</label>
                  <input id="trigger-delay-input" bind:value={triggerDelay} type="number" class="w-full px-3 py-1.5 rounded bg-[#0f0e0d] border border-[#3d3831] text-xs font-mono text-white" />
                </div>
              </div>
            {:else}
              <div class="space-y-1.5">
                <label for="trigger-value-input" class="text-[11px] text-[#a39e95]">Значение (Секунды / Скорость / Проценты)</label>
                <input id="trigger-value-input" bind:value={triggerValue} type="number" class="w-full px-3 py-2 rounded-lg bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs font-mono text-white outline-none" />
              </div>
            {/if}

            <div class="flex items-center gap-2 mt-4 pt-2 border-t border-[#2d2924]">
              <input type="checkbox" id="is-passive" bind:checked={isPassive} class="w-4 h-4 accent-amber-500 cursor-pointer" />
              <label for="is-passive" class="text-[11px] text-[#a39e95] cursor-pointer leading-tight">
                <strong class="text-white">Скрытое событие (Без вызова)</strong><br>Не зажигать лампочку. Проводник должен заметить сам (увидит или услышит).
              </label>
            </div>
          </div>
        </div>

        <!-- ПРАВАЯ КОЛОНКА: ИИ И ПОВЕДЕНИЕ -->
        <div class="p-4 rounded-xl bg-gradient-to-br from-[#1a1816] to-[#12110f] border border-amber-900/30 space-y-4">
          <h3 class="text-xs font-bold text-amber-400 uppercase tracking-wider border-b border-amber-900/30 pb-1 flex items-center gap-2">
            <span>🧠 3. Состояние и ИИ-Инструкция</span>
          </h3>

          <div class="space-y-1.5">
            <label for="passenger-state-select" class="text-[11px] text-[#a39e95]">Анимация / Аудио-тег в вагоне</label>
            <select id="passenger-state-select" bind:value={passengerState} class="w-full px-3 py-2 rounded-lg bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-white outline-none">
              <option value="vaping">💨 Курит Вейп (Визуальный дым)</option>
              <option value="crying_child">😭 Плач ребенка (Пространственное аудио)</option>
              <option value="drunk">🍺 Нетрезвый (Покачивание)</option>
              <option value="sleeping">💤 Спит (Zzz)</option>
              <option value="annoyed">😤 Недоволен / Злой</option>
            </select>
          </div>
          
          <div class="space-y-1.5">
            <label for="llm-system-prompt-textarea" class="text-[11px] text-[#a39e95]">Промпт для нейросети (Роль и характер)</label>
            <textarea id="llm-system-prompt-textarea" bind:value={llmSystemPrompt} rows="4" class="w-full px-3.5 py-2.5 rounded-xl bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-emerald-300 italic outline-none leading-relaxed" placeholder="Опиши, как пассажир должен отвечать..."></textarea>
          </div>

          <div class="space-y-1.5">
            <label for="expected-rule-textarea" class="text-[11px] text-[#a39e95]">Критерий успеха (Эталонный ответ проводника)</label>
            <textarea id="expected-rule-textarea" bind:value={expectedRule} rows="3" class="w-full px-3.5 py-2.5 rounded-xl bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-amber-300 outline-none leading-relaxed" placeholder="Укажи правила или алгоритм, который ИИ будет искать в ответе игрока..."></textarea>
          </div>
        </div>

      </div>

      <div class="flex justify-end pt-4 border-t border-[#2d2924]">
        <button onclick={handleSaveScenario} disabled={isSaving} class="px-8 py-3.5 rounded-xl bg-gradient-to-r from-amber-600 via-amber-500 to-yellow-500 hover:from-amber-500 text-stone-950 font-bold text-xs sm:text-sm tracking-wide shadow-lg shadow-amber-500/20 cursor-pointer transition-all flex items-center gap-2 hover:scale-105 active:scale-95">
          <span>{isSaving ? '⏳ Добавление...' : '🚀 Зарегистрировать событие'}</span>
        </button>
      </div>
    </div>

  {:else}
    <!-- Заглушка базы знаний -->
    <div class="p-5 rounded-2xl bg-[#1a1816] border border-[#2d2924] text-xs text-[#a39e95]">
      База знаний стандартов в режиме разработки.
    </div>
  {/if}
</div>
