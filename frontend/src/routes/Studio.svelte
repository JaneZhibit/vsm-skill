<script lang="ts">
  import { onMount } from 'svelte';
  import { playClickSound, playSuccessSound, playErrorSound } from '../lib/utils/audio';

  let activeTab = $state<'cases' | 'handbook' | 'constructor'>('constructor');

  // --- ДАННЫЕ РЕДАКТОРА ---
  let customTitle = $state<string>('');
  let targetArchetype = $state<string>('any');
  
  // Триггеры
  let triggerType = $state<'orchestrator' | 'chained' | 'test'>('orchestrator');
  let triggerParentId = $state<string>('');
  let triggerDelay = $state<number>(15);
  let triggerCondition = $state<'ignored' | 'resolved'>('ignored'); // ФАЗА СРАБАТЫВАНИЯ

  // Визуал и Аудио
  let isPassive = $state<boolean>(false);
  let ambientAudio = $state<string>('');
  let previewAudioObj = $state<HTMLAudioElement | null>(null);
  let isUploadingAudio = $state<boolean>(false);

  // Компетенции
  let skills = $state<Record<string, boolean>>({ safety: false, service: true, medicine: false, discipline: false });

  // ИИ (LLM) и Эмоции
  let allowedMoods = $state<string[]>(['neutral']);
  let activePreviewMood = $state<string>('neutral'); // Что сейчас показываем крупно
  let llmSystemPrompt = $state<string>('');
  let expectedRule = $state<string>('');

  // Состояние UI
  let isSaving = $state<boolean>(false);
  let successMessage = $state<string | null>(null);
  let errorMessage = $state<string | null>(null);
  let existingScenarios = $state<{id: string, title: string}[]>([]);

  // Словари для UI
  const MOODS_MAP: Record<string, string[]> = {
    'male_young': ['neutral', 'angry', 'happy', 'sleeping', 'sick', 'drunk', 'vaping_calm', 'vaping_angry', 'crying'],
    'female_young': ['neutral', 'happy', 'annoyed', 'sleeping', 'sick', 'reading', 'gadget'],
    'female_elderly': ['neutral', 'reading', 'sleeping', 'annoyed', 'happy', 'sick'],
    'any': ['neutral', 'angry', 'happy', 'sleeping', 'sick', 'annoyed']
  };
  let currentAvailableMoods = $derived(MOODS_MAP[targetArchetype] || MOODS_MAP['any']);
  let AUDIO_FILES = $state([
    { id: '', label: '🔇 Без звука' },
    { id: 'crying_child.mp3', label: '😭 Плач ребенка' },
    { id: 'vape_hiss.mp3', label: '💨 Шипение вейпа' },
    { id: 'kid_playing.mp3', label: '📱 Звуки мобильной игры' },
  ]);

  // --- РЕАКТИВНЫЙ ПРЕВЬЮ ПАССАЖИРА ---
  let previewArchetype = $derived(targetArchetype === 'any' ? 'male_young' : targetArchetype);
  let previewImageUrl = $derived(`/assets/${previewArchetype}/${activePreviewMood}.png`);

  onMount(async () => {
    // Загружаем список существующих событий для "Цепной реакции"
    try {
      const res = await fetch('/api/v1/simulation/custom-live-scenario');
      if (res.ok) {
        existingScenarios = await res.json();
      }
    } catch {}
  });

  // Загрузка своего аудио
  async function handleAudioUpload(e: Event) {
    const input = e.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;
    
    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    isUploadingAudio = true;
    try {
      const res = await fetch('/api/v1/simulation/upload-ambient-audio', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        AUDIO_FILES = [...AUDIO_FILES, { id: data.filename, label: `🎵 ${data.filename}` }];
        ambientAudio = data.filename;
        playSuccessSound();
      } else {
        throw new Error();
      }
    } catch {
      playErrorSound();
      alert("Ошибка загрузки аудио");
    } finally {
      isUploadingAudio = false;
      input.value = '';
    }
  }

  function toggleAudioPreview() {
    if (!ambientAudio) return;
    if (previewAudioObj) {
      previewAudioObj.pause();
      previewAudioObj = null;
    } else {
      previewAudioObj = new Audio(`/storage/audio/ambient/${ambientAudio}`);
      previewAudioObj.volume = 0.5;
      previewAudioObj.loop = true;
      previewAudioObj.play().catch(() => {});
    }
  }

  function toggleMoodSelection(mood: string) {
    playClickSound();
    if (allowedMoods.includes(mood)) {
      if (allowedMoods.length > 1) {
        allowedMoods = allowedMoods.filter(m => m !== mood);
      }
    } else {
      allowedMoods = [...allowedMoods, mood];
    }
  }

  async function handleSaveScenario() {
    playClickSound();
    isSaving = true;
    successMessage = null;
    errorMessage = null;

    const selectedSkills = Object.entries(skills).filter(([_, val]) => val).map(([key]) => key);

    const payload = {
      incident_id: `evt_${Date.now()}`,
      title: customTitle.trim() || 'Новое событие',
      target_archetype: targetArchetype,
      trigger: {
        type: triggerType,
        parent_id: triggerType === 'chained' ? triggerParentId : null,
        delay_sec: Number(triggerDelay),
        condition: triggerCondition
      },
      allowed_moods: allowedMoods,
      ambient_audio: ambientAudio || null,
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
        playSuccessSound();
        successMessage = triggerType === 'test' 
          ? 'Тестовое событие готово! Запустите PRO-Рейс, оно сработает по таймеру.'
          : 'Событие добавлено в пул GameMaster!';
        
        const json = await res.json();
        existingScenarios = [...existingScenarios, { id: json.incident_id || payload.incident_id, title: payload.title }];
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
</script>

<div class="w-full max-w-[1200px] mx-auto p-4 sm:p-6 flex flex-col gap-6 selection:bg-amber-500 selection:text-black">
  <header class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#2d2924] pb-4">
    <div>
      <h1 class="text-xl font-bold text-[#f5f3ef] tracking-wide">Режиссер Симуляции (Event Builder)</h1>
      <p class="text-xs text-[#a39e95] mt-0.5">Создание нелинейных ИИ-событий для PRO-режима</p>
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
    {#if successMessage}
      <div class="p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 text-sm font-bold flex items-center gap-2.5">✅ {successMessage}</div>
    {/if}
    {#if errorMessage}
      <div class="p-3.5 rounded-xl bg-rose-950/60 border border-rose-500/50 text-rose-300 text-sm font-bold flex items-center gap-2.5">❌ {errorMessage}</div>
    {/if}

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start mt-2">
      
      <!-- 1. АКТЕР И ВИЗУАЛ (Галерея) -->
      <div class="lg:col-span-4 space-y-4">
        <div class="p-5 rounded-2xl bg-[#141210] border border-[#2d2924] shadow-lg flex flex-col gap-4">
          <h3 class="text-xs font-bold text-amber-400 uppercase tracking-wider border-b border-[#2d2924] pb-2">1. Актер и Визуализация</h3>
          
          <div class="space-y-1.5">
            <label for="custom-title-input" class="text-[11px] text-[#a39e95]">Название события</label>
            <input id="custom-title-input" bind:value={customTitle} type="text" class="w-full px-3 py-2 rounded-lg bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-white outline-none transition-all" placeholder="Например: Пьяный сосед" />
          </div>

          <div class="space-y-1.5">
            <label for="target-archetype-select" class="text-[11px] text-[#a39e95]">Архетип (Кто это?)</label>
            <select id="target-archetype-select" bind:value={targetArchetype} class="w-full px-3 py-2 rounded-lg bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-white outline-none">
              <option value="any">🎲 Любой случайный (Auto)</option>
              <option value="male_young">👨 Молодой парень</option>
              <option value="female_young">👩 Девушка</option>
              <option value="female_elderly">👵 Пожилая женщина</option>
            </select>
          </div>

          <!-- Главное превью -->
          <div class="w-full aspect-[4/3] bg-[#0a0908] rounded-xl border border-[#2d2924] relative overflow-hidden flex items-center justify-center shadow-inner">
            <div class="absolute top-2 left-2 px-2 py-0.5 bg-black/60 rounded text-[9px] text-[#706b63] border border-[#2d2924] z-10 backdrop-blur-md">
              Превью ({activePreviewMood})
            </div>
            <img 
              src={previewImageUrl} 
              alt="Превью" 
              class="h-[85%] object-contain opacity-90 transition-all duration-300" 
              onerror={(e) => { const img = e.currentTarget as HTMLImageElement; img.src = `/assets/${previewArchetype}/neutral.png`; }} 
            />
          </div>

          <!-- Галерея эмоций -->
          <div>
            <div class="text-[11px] text-[#a39e95] mb-2 block">Доступные эмоции для ИИ (Выберите нужные):</div>
            <div class="grid grid-cols-4 gap-2">
              {#each currentAvailableMoods as mood}
                <!-- svelte-ignore a11y_click_events_have_key_events -->
                <!-- svelte-ignore a11y_no_static_element_interactions -->
                <div 
                  class="relative aspect-square bg-[#0f0e0d] rounded-lg border-2 cursor-pointer transition-all overflow-hidden group {allowedMoods.includes(mood) ? 'border-amber-500' : 'border-transparent hover:border-[#3d3831]'}"
                  onclick={() => { activePreviewMood = mood; }}
                >
                  <!-- Маленькая превьюшка -->
                  <img 
                    src={`/assets/${previewArchetype}/${mood}.png`} 
                    class="w-full h-full object-cover opacity-80 group-hover:opacity-100" 
                    onerror={(e) => { const img = e.currentTarget as HTMLImageElement; img.src = `/assets/${previewArchetype}/neutral.png`; }} 
                    alt={mood}
                  />
                  
                  <!-- Чекбокс включения в пул -->
                  <div class="absolute bottom-1 right-1 bg-black/80 rounded border border-[#3d3831] p-0.5 z-10">
                    <input 
                      type="checkbox" 
                      checked={allowedMoods.includes(mood)} 
                      onchange={() => toggleMoodSelection(mood)} 
                      class="w-3 h-3 accent-amber-500 cursor-pointer" 
                      title="Включить в список ИИ" 
                    />
                  </div>
                  <!-- Лейбл (показывается при наведении) -->
                  <div class="absolute top-0 left-0 w-full bg-black/70 text-[8px] text-center text-white py-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    {mood}
                  </div>
                </div>
              {/each}

              <!-- Кнопка-плейсхолдер генерации нового стейта -->
              <button 
                onclick={() => alert("Генерация новых состояний через Midjourney/Flux API в разработке для хакатона!")} 
                class="aspect-square rounded-lg border border-dashed border-[#3d3831] hover:border-amber-500/60 bg-[#0f0e0d]/50 hover:bg-[#1a1816] flex flex-col items-center justify-center p-1 text-center transition-all group cursor-pointer"
                title="Сгенерировать новое состояние персонажа нейросетью"
              >
                <span class="text-base group-hover:scale-110 transition-transform">✨</span>
                <span class="text-[8px] text-stone-400 group-hover:text-amber-300 font-medium leading-tight mt-1">Создать свой стейт</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. ТРИГГЕРЫ И ОКРУЖЕНИЕ -->
      <div class="lg:col-span-4 space-y-4">
        <div class="p-5 rounded-2xl bg-[#141210] border border-[#2d2924] shadow-lg flex flex-col gap-5">
          <h3 class="text-xs font-bold text-emerald-400 uppercase tracking-wider border-b border-[#2d2924] pb-2">2. Логика срабатывания и Окружение</h3>
          
          <div class="space-y-3">
            <label class="flex items-start gap-2.5 p-3 rounded-xl border cursor-pointer transition-all {triggerType === 'orchestrator' ? 'bg-emerald-950/20 border-emerald-500/50' : 'bg-[#0f0e0d] border-[#2d2924]'}">
              <input type="radio" bind:group={triggerType} value="orchestrator" class="mt-0.5 accent-emerald-500" />
              <div>
                <div class="text-xs font-bold text-white">🧠 Решает Оркестратор</div>
                <div class="text-[10px] text-[#706b63] leading-tight mt-0.5">GameMaster сам решит, когда запустить по ходу рейса.</div>
              </div>
            </label>

            <label class="flex items-start gap-2.5 p-3 rounded-xl border cursor-pointer transition-all {triggerType === 'chained' ? 'bg-indigo-950/20 border-indigo-500/50' : 'bg-[#0f0e0d] border-[#2d2924]'}">
              <input type="radio" bind:group={triggerType} value="chained" class="mt-0.5 accent-indigo-500" />
              <div class="w-full">
                <div class="text-xs font-bold text-indigo-300 mb-1">🔗 Цепная реакция (Следствие)</div>
                {#if triggerType === 'chained'}
                  <div class="space-y-2 mt-2">
                    <select bind:value={triggerParentId} class="w-full px-2 py-1.5 rounded bg-black border border-indigo-500/30 text-xs text-white outline-none">
                      <option value="" disabled>-- Родительское событие --</option>
                      {#each existingScenarios as sc}
                        <option value={sc.id}>{sc.title}</option>
                      {/each}
                    </select>
                    
                    <select bind:value={triggerCondition} class="w-full px-2 py-1.5 rounded bg-black border border-indigo-500/30 text-xs text-white outline-none">
                      <option value="ignored">❌ Если родитель ИГНОРИРОВАЛСЯ</option>
                      <option value="resolved">✅ Если родитель был РЕШЕН</option>
                    </select>

                    <div class="flex items-center justify-between text-xs text-indigo-300">
                      <span>Спустя:</span>
                      <div class="flex items-center gap-1">
                        <input bind:value={triggerDelay} type="number" class="w-16 px-2 py-1 rounded bg-black border border-indigo-500/30 font-mono text-white text-center outline-none text-xs" />
                        <span>сек</span>
                      </div>
                    </div>
                  </div>
                {/if}
              </div>
            </label>

            <label class="flex items-start gap-2.5 p-3 rounded-xl border cursor-pointer transition-all {triggerType === 'test' ? 'bg-rose-950/20 border-rose-500/50' : 'bg-[#0f0e0d] border-[#2d2924]'}">
              <input type="radio" bind:group={triggerType} value="test" class="mt-0.5 accent-rose-500" />
              <div class="flex-1 flex items-center justify-between">
                <div class="text-xs font-bold text-rose-300">⏱️ Тест: через</div>
                <input bind:value={triggerDelay} type="number" class="w-14 px-1 py-1 rounded bg-black border border-rose-500/30 text-xs font-mono text-white text-center outline-none" />
                <span class="text-[10px] text-rose-300/70">сек</span>
              </div>
            </label>
          </div>

          <!-- Аудио и Скрытность -->
          <div class="space-y-4 pt-2 border-t border-[#2d2924]">
            <div class="space-y-2">
              <label for="ambient-audio-select" class="text-[11px] text-[#a39e95]">Окружающий звук (Ambient)</label>
              <div class="flex flex-col gap-2">
                <div class="flex items-center gap-2">
                  <select id="ambient-audio-select" bind:value={ambientAudio} class="flex-1 px-3 py-2 rounded-lg bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-white outline-none truncate">
                    {#each AUDIO_FILES as af}
                      <option value={af.id}>{af.label}</option>
                    {/each}
                  </select>
                  {#if ambientAudio}
                    <button type="button" onclick={toggleAudioPreview} class="w-9 h-9 flex items-center justify-center rounded-lg bg-[#282420] border border-[#3d3831] text-amber-400 hover:bg-[#3d3831] transition-colors cursor-pointer shrink-0" title="Прослушать звук">
                      {previewAudioObj ? '⏹️' : '🔊'}
                    </button>
                  {/if}
                </div>
                <!-- Загрузка своего аудио -->
                <label class="flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg border border-dashed border-[#3d3831] bg-[#0f0e0d] hover:border-amber-500/50 hover:text-amber-300 text-[10px] text-[#706b63] cursor-pointer transition-colors">
                  <span>{isUploadingAudio ? 'Загрузка...' : '📁 Загрузить свой .mp3'}</span>
                  <input type="file" accept="audio/*" class="hidden" onchange={handleAudioUpload} disabled={isUploadingAudio} />
                </label>
              </div>
            </div>

            <label class="flex items-center gap-3 p-3 rounded-xl bg-[#0f0e0d] border border-[#2d2924] cursor-pointer">
              <input type="checkbox" bind:checked={isPassive} class="w-4 h-4 accent-amber-500" />
              <div class="text-xs text-stone-300 leading-tight">
                <strong class="text-white">Скрытое событие (Без вызова 🔔)</strong><br>
                <span class="text-[9px] text-[#706b63]">Игрок должен сам заметить визуал или аудио.</span>
              </div>
            </label>

            <!-- Теги компетенций -->
            <div class="pt-2 border-t border-[#2d2924]">
              <label for="skills-list" class="text-[10px] font-bold text-[#706b63] uppercase tracking-wider block mb-2">Развиваемые навыки</label>
              <div id="skills-list" class="flex flex-wrap gap-1.5">
                {#each Object.keys(skills) as skill}
                  <label class="flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-mono border cursor-pointer transition-all {skills[skill] ? 'bg-[#282420] border-amber-500 text-amber-300' : 'bg-[#0f0e0d] border-[#2d2924] text-[#706b63]'}">
                    <input type="checkbox" bind:checked={skills[skill]} class="hidden" /> {skill}
                  </label>
                {/each}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. ИНСТРУКЦИИ ИИ (LLM) -->
      <div class="lg:col-span-4 space-y-4">
        <div class="p-5 rounded-2xl bg-gradient-to-br from-[#1a1816] to-[#141210] border border-amber-900/40 shadow-[0_0_20px_rgba(245,158,11,0.05)] flex flex-col gap-4 h-full">
          <h3 class="text-xs font-bold text-amber-400 uppercase tracking-wider border-b border-amber-900/30 pb-2">3. Инструкции ИИ-Агенту (LLM)</h3>
          
          <div class="space-y-1.5">
            <label for="llm-prompt-textarea" class="text-[11px] text-[#a39e95]">Системный промпт (Роль, Характер, Ситуация)</label>
            <textarea id="llm-prompt-textarea" bind:value={llmSystemPrompt} rows="6" class="w-full px-3.5 py-2.5 rounded-xl bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-emerald-300 italic outline-none leading-relaxed resize-none shadow-inner" placeholder="Ты - недовольный пассажир. Если проводник вежливо просит..."></textarea>
            <p class="text-[9px] text-[#706b63]">ИИ автоматически получит профиль пассажира и пол проводника. Опишите только суть инцидента.</p>
          </div>

          <div class="space-y-1.5 flex-1">
            <label for="expected-rule-textarea" class="text-[11px] text-[#a39e95]">Критерий успеха (Эталонный ответ проводника)</label>
            <textarea id="expected-rule-textarea" bind:value={expectedRule} rows="5" class="w-full h-[calc(100%-20px)] px-3.5 py-2.5 rounded-xl bg-[#0f0e0d] border border-[#3d3831] focus:border-amber-400 text-xs text-amber-300 outline-none leading-relaxed resize-none shadow-inner" placeholder="Правило: Вежливо извиниться и предложить..."></textarea>
          </div>
        </div>
      </div>
    </div>

    <div class="flex justify-end mt-2 pt-4 border-t border-[#2d2924]">
      <button onclick={handleSaveScenario} disabled={isSaving} class="px-8 py-3.5 rounded-xl bg-gradient-to-r from-amber-600 via-amber-500 to-yellow-500 hover:from-amber-500 text-stone-950 font-bold text-sm tracking-wide shadow-lg shadow-amber-500/20 cursor-pointer transition-all flex items-center gap-2 hover:scale-105 active:scale-95 disabled:opacity-50">
        <span>{isSaving ? '⏳ Добавление...' : '💾 Зарегистрировать событие'}</span>
      </button>
    </div>
  {:else}
    <!-- Заглушка базы знаний -->
    <div class="p-5 rounded-2xl bg-[#1a1816] border border-[#2d2924] text-xs text-[#a39e95]">
      База знаний стандартов в режиме разработки.
    </div>
  {/if}
</div>
