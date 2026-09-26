<script lang="ts">
  import { playClickSound, playSuccessSound, playErrorSound } from '../lib/utils/audio';

  let activeTab = $state<'cases' | 'handbook' | 'constructor'>('constructor');

  // --- ПОЛЯ НОВОГО СОБЫТИЙНОГО РЕДАКТОРА ---
  let customTitle = $state<string>('Пассажир курит вейп в кресле');
  let targetArchetype = $state<string>('any');
  
  let triggerType = $state<string>('time');
  let triggerValue = $state<number>(15); // Через сколько секунд после старта сработает

  let passengerState = $state<string>('vaping');
  let isPassive = $state<boolean>(true); // Без красного колокольчика
  
  let llmSystemPrompt = $state<string>('Ты куришь электронную сигарету. Если проводник вежливо просит убрать её, сославшись на датчики дыма - извинись и убери. Если хамит - скандаль.');
  let expectedRule = $state<string>('Запрет курения (в т.ч. электронных сигарет) по требованиям пожарной безопасности. СТО РЖД п. 4.1.2.');

  let isSaving = $state<boolean>(false);
  let successMessage = $state<string | null>(null);
  let errorMessage = $state<string | null>(null);

  async function handleSaveScenario() {
    playClickSound();
    isSaving = true;
    successMessage = null;
    errorMessage = null;

    const payload = {
      incident_id: `live_evt_${Date.now()}`,
      title: customTitle.trim(),
      target_archetype: targetArchetype,
      trigger: {
        type: triggerType,
        value: Number(triggerValue)
      },
      passenger_state: passengerState,
      is_passive: isPassive,
      llm_system_prompt: llmSystemPrompt.trim(),
      expected_rule: expectedRule.trim()
    };

    try {
      const res = await fetch('/api/v1/simulation/custom-live-scenario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        playSuccessSound();
        successMessage = 'Эмерджентное событие добавлено! Запустите PRO-Рейс, чтобы проверить.';
      } else {
        throw new Error(`Ошибка сервера: ${res.status}`);
      }
    } catch (err: any) {
      playErrorSound();
      errorMessage = err?.message || 'Не удалось сохранить событие';
    } finally {
      isSaving = false;
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
            <span>🎭 Настройка живого микро-сценария</span>
          </h2>
          <p class="text-[11px] text-[#a39e95] mt-1">Определите параметры пассажира, триггер срабатывания и ИИ-поведение.</p>
        </div>
      </div>

      {#if successMessage}
        <div class="p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 text-xs flex items-center gap-2.5">✅ {successMessage}</div>
      {/if}
      {#if errorMessage}
        <div class="p-3.5 rounded-xl bg-rose-950/60 border border-rose-500/50 text-rose-300 text-xs flex items-center gap-2.5">❌ {errorMessage}</div>
      {/if}

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- БЛОК 1: КТО (Целевой пассажир) -->
        <div class="p-4 rounded-xl bg-[#1a1816] border border-[#3d3831] space-y-3">
          <h3 class="text-xs font-bold text-stone-300 uppercase tracking-wider mb-2 border-b border-[#2d2924] pb-1">1. Кто генерирует событие</h3>
          
          <div class="space-y-1.5">
            <label class="text-[11px] text-[#a39e95]">Название события (для логов)</label>
            <input bind:value={customTitle} type="text" class="w-full px-3 py-2 rounded-lg bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-white outline-none" />
          </div>

          <div class="space-y-1.5">
            <label class="text-[11px] text-[#a39e95]">Тип пассажира (Archetype)</label>
            <select bind:value={targetArchetype} class="w-full px-3 py-2 rounded-lg bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-white outline-none">
              <option value="any">🎲 Любой случайный пассажир</option>
              <option value="male_young">👨 Молодой мужчина</option>
              <option value="female_young">👩 Молодая девушка</option>
              <option value="female_elderly">👵 Пожилая женщина</option>
            </select>
          </div>
        </div>

        <!-- БЛОК 2: КОГДА (Триггер) -->
        <div class="p-4 rounded-xl bg-[#1a1816] border border-[#3d3831] space-y-3">
          <h3 class="text-xs font-bold text-stone-300 uppercase tracking-wider mb-2 border-b border-[#2d2924] pb-1">2. Когда сработает (Триггер)</h3>
          
          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1.5">
              <label class="text-[11px] text-[#a39e95]">Условие</label>
              <select bind:value={triggerType} class="w-full px-3 py-2 rounded-lg bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-white outline-none">
                <option value="time">⏱ По таймеру (сек)</option>
                <option value="speed">🚄 По скорости (км/ч)</option>
              </select>
            </div>
            <div class="space-y-1.5">
              <label class="text-[11px] text-[#a39e95]">Значение триггера</label>
              <input bind:value={triggerValue} type="number" class="w-full px-3 py-2 rounded-lg bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs font-mono text-amber-300 outline-none" />
            </div>
          </div>

          <div class="flex items-center gap-2 mt-4">
            <input type="checkbox" id="is-passive" bind:checked={isPassive} class="w-4 h-4 accent-amber-500 cursor-pointer" />
            <label for="is-passive" class="text-xs text-[#a39e95] cursor-pointer">
              <strong class="text-white">Скрытое событие</strong> (Не зажигать лампочку вызова. Проводник должен заметить сам).
            </label>
          </div>
        </div>

        <!-- БЛОК 3: ИИ-ПОВЕДЕНИЕ -->
        <div class="md:col-span-2 p-4 rounded-xl bg-gradient-to-br from-[#1a1816] to-[#12110f] border border-amber-900/30 space-y-4">
          <h3 class="text-xs font-bold text-amber-400 uppercase tracking-wider border-b border-amber-900/30 pb-1 flex items-center gap-2">
            <span>🧠 3. Инструкция для LLM (Prompt Engineering)</span>
          </h3>

          <div class="space-y-1.5">
            <label class="text-[11px] text-[#a39e95]">Внешнее состояние (Визуализация в салоне)</label>
            <select bind:value={passengerState} class="w-full px-3 py-2 rounded-lg bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-white outline-none max-w-xs">
              <option value="vaping">💨 Курит Вейп (vaping)</option>
              <option value="crying_child">😭 Плач ребенка (crying)</option>
              <option value="drunk">🍺 Нетрезвый (drunk)</option>
              <option value="sleeping">💤 Спит (sleeping)</option>
              <option value="annoyed">😤 Недоволен (annoyed)</option>
            </select>
          </div>
          
          <div class="space-y-1.5">
            <label class="text-[11px] text-[#a39e95]">System Prompt: Что ИИ должен отыгрывать (Роль и характер)</label>
            <textarea bind:value={llmSystemPrompt} rows="3" class="w-full px-3.5 py-2.5 rounded-xl bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-emerald-300 italic outline-none leading-relaxed"></textarea>
          </div>

          <div class="space-y-1.5">
            <label class="text-[11px] text-[#a39e95]">Критерий успеха: Что ожидается от проводника (Для оценки)</label>
            <textarea bind:value={expectedRule} rows="2" class="w-full px-3.5 py-2.5 rounded-xl bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-amber-300 outline-none leading-relaxed"></textarea>
          </div>
        </div>
      </div>

      <div class="flex justify-end pt-3 border-t border-[#2d2924]">
        <button onclick={handleSaveScenario} disabled={isSaving} class="px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 text-white font-bold text-xs sm:text-sm tracking-wide shadow-lg shadow-emerald-500/20 cursor-pointer transition-all flex items-center gap-2">
          <span>{isSaving ? '⏳ Инъекция в БД...' : '🚀 Активировать событие'}</span>
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
