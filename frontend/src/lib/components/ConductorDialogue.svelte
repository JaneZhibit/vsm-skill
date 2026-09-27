<script lang="ts">
  import { onDestroy } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { trainWorld } from '../stores/trainWorld.svelte';
  import { trainAudio } from '../stores/trainAudio.svelte';
  import { conductorState } from '../stores/conductorState.svelte';
  import type { ActiveIncident } from '../config/cabinConfig';
  import { playSuccessSound, playErrorSound, playClickSound } from '../utils/audio';

  type Stage = 'decision' | 'feedback' | 'learning_card';

  let currentSeat = $derived(trainWorld.selectedSeat);
  let activeIncident = $derived(currentSeat?.activeIncident);
  let dialogIncident = $state<ActiveIncident | null>(trainWorld.selectedSeat?.activeIncident || null);
  let currentIncident = $derived<ActiveIncident | null>(dialogIncident || activeIncident || null);
  
  let currentStepId = $state<string>('step_1');
  let currentStep = $derived<any>(currentIncident?.steps?.[currentStepId] || currentIncident || { options: [] });

  let isEditingVoice = $state<boolean>(false);
  let editableTranscript = $state<string>('');

  // --- ЛОГИКА РЕЖИМОВ ---
  let isProMode = $derived(trainWorld.tripMode === 'pro');
  let conductorGender = $derived(conductorState.conductorProfile.gender);

  let stage = $state<Stage>('decision');
  let timeLeft = $state<number>(0);
  let selectedOption = $state<any>(null);
  let pendingNextStep = $state<string | null>(null);
  let isTimeout = $state<boolean>(false);
  let timerInterval: ReturnType<typeof setInterval> | null = null;
  let feedbackResult = $state<any>(null);

  // --- ГОЛОС (Web Speech API - Распознавание в браузере) ---
  let isRecording = $state<boolean>(false);
  let recordingSeconds = $state<number>(0);
  let recordingTimer: ReturnType<typeof setInterval> | null = null;
  let isAnalyzingVoice = $state<boolean>(false);
  let micError = $state<string | null>(null);
  
  let recognition: any = null;
  let finalTranscript = $state<string>('');
  let interimTranscript = $state<string>('');

  // --- ДАННЫЕ UI ---
  let formattedSeconds = $derived(Math.ceil(timeLeft).toString().padStart(2, '0'));
  let formattedRecordTimer = $derived(`00:${recordingSeconds.toString().padStart(2, '0')}`);
  let passengerName = $derived(currentSeat?.isOccupied ? (currentSeat.passenger?.full_name || 'Пассажир') : 'Свободное место');

  // Динамические кнопки (Добавляем помощь для девушек)
  let dynamicOptions = $derived.by(() => {
    let opts = currentStep?.options || currentIncident?.options || [];
    if (!isProMode && currentIncident?.incident_id === 'inc_luggage_aisle_01' && conductorGender === 'f') {
      if (!opts.find((o: any) => o.id === 'opt_ask_male')) {
        opts = [...opts, {
          id: 'opt_ask_male',
          text: '«Мужчина, не могли бы вы помочь закинуть чемодан пассажиру?»',
          action_type: 'click',
          result: {
            loyalty_delta: 20, safety_delta: 30, mood: 'calm',
            feedback: "Отличная работа! Вы делегировали тяжелую физическую работу, сохранив свое здоровье и решив проблему безопасности (СТО РЖД)."
          }
        }];
      }
    }
    return opts;
  });

  // --- ТЕКСТ ДИАЛОГА (МГНОВЕННЫЙ И РЕАКТИВНЫЙ) ---
  let fullDialogueText = $derived.by(() => {
    // 1. Если мы на этапе разбора - выводим ответ пассажира
    if (stage === 'feedback') {
      if (feedbackResult?.passenger_reply) {
        const reply = feedbackResult.passenger_reply;
        return reply.startsWith('«') ? reply : `«${reply}»`;
      }
      if (feedbackResult?.feedback) {
        return `«${feedbackResult.feedback}»`;
      }
      return '';
    }
    // 2. Если есть активный инцидент - выводим заготовленный промпт
    const inc = currentIncident;
    if (inc) {
      const rawPrompt = currentStep?.prompt ?? inc?.prompt;
      if (rawPrompt) {
        if (typeof rawPrompt === 'object' && rawPrompt !== null) {
          const archId = currentSeat?.passenger?.archetype_id || 'male_young';
          const trait = currentSeat?.passenger?.trait || 'polite';
          return rawPrompt[`${archId}_${trait}`] || rawPrompt[trait] || rawPrompt[archId] || rawPrompt['default'] || '';
        }
        return String(rawPrompt);
      }
    }
    // 3. Иначе - пассажир молчит!
    return ''; 
  });

  let displayedText = $derived(fullDialogueText);

  // --- УПРАВЛЕНИЕ ЖИЗНЕННЫМ ЦИКЛОМ ИНЦИДЕНТА ---
  let currentSeatId = $derived(currentSeat?.id);
  let boundSeatId = trainWorld.selectedSeat?.id || '';
  let initializedIncidentId = '';

  $effect(() => {
    // Смена выбранного кресла проводником
    if (currentSeatId !== boundSeatId) {
      boundSeatId = currentSeatId || '';
      initializedIncidentId = '';
      resetDialogState();
    }

    // Инициализация инцидента на выбранном кресле
    if (activeIncident && stage === 'decision') {
      if (activeIncident.incident_id !== initializedIncidentId) {
        initializedIncidentId = activeIncident.incident_id;
        dialogIncident = activeIncident;
        currentStepId = activeIncident.start_step || 'step_1';
        timeLeft = currentStep?.timer_seconds || activeIncident.timer_seconds || 30;
        trainAudio.setAmbientDucking(true);
        if (currentSeat?.passenger) {
          trainWorld.playPassengerDialog(
            activeIncident.incident_id,
            currentSeat.passenger.archetype_id,
            currentSeat.passenger.trait
          );
        }
        startTimer();
      }
    }
  });

  function resetDialogState() {
    dialogIncident = null;
    initializedIncidentId = '';
    stopTimer();
    stopRecording(false);
    stage = 'decision';
    currentStepId = 'step_1';
    feedbackResult = null;
    isTimeout = false;
    isEditingVoice = false;
    editableTranscript = '';
    trainAudio.setAmbientDucking(false);
  }

  // --- ТАЙМЕРЫ ---
  function startTimer() {
    isTimeout = false;
    stopTimer();
    timerInterval = setInterval(() => {
      if (stage !== 'decision') return;
      if (timeLeft > 0.1) timeLeft = Math.max(0, Math.round((timeLeft - 0.1) * 10) / 10);
      else triggerTimeout();
    }, 100);
  }
  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  async function triggerTimeout() {
    const incId = currentIncident?.incident_id;
    if (!incId) return;
    stopTimer();
    stopRecording();
    isTimeout = true;
    stage = 'feedback';
    playErrorSound();
    feedbackResult = await trainWorld.resolveIncident(incId, 'opt_timeout');
  }

  // --- ЛОГИКА ДЕЙСТВИЙ ---
  async function executeOption(opt: any) {
    if (opt.why_correct || opt.what_if_wrong) {
      selectedOption = opt;
      if (opt.next_step) {
        stopTimer();
        pendingNextStep = opt.next_step;
        stage = 'learning_card';
        playClickSound();
        return;
      }
    }
    if (opt.next_step) {
      currentStepId = opt.next_step;
      timeLeft = currentIncident?.steps?.[opt.next_step]?.timer_seconds || 30;
      playClickSound();
    } else {
      stopTimer();
      stage = 'feedback';
      const incId = currentIncident?.incident_id;
      if (incId) {
        feedbackResult = await trainWorld.resolveIncident(incId, opt.id);
      }
      if (feedbackResult?.loyalty_delta > 0 || feedbackResult?.is_passed) playSuccessSound(); else playErrorSound();
    }
  }

  // --- ЛОГИКА ГОЛОСА (Web Speech API) ---
  async function startRecording() {
    stopTimer();
    micError = null;
    finalTranscript = '';
    interimTranscript = '';

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      micError = 'Ваш браузер не поддерживает распознавание речи (используйте Chrome/Edge).';
      playErrorSound();
      return;
    }

    if (!recognition) {
      recognition = new SpeechRecognition();
      recognition.lang = 'ru-RU';
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onresult = (event: any) => {
        let interim = '';
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            final += transcript + ' ';
          } else {
            interim += transcript;
          }
        }
        finalTranscript += final;
        interimTranscript = interim;
      };

      recognition.onerror = (event: any) => {
        if (event.error === 'not-allowed') micError = 'Доступ к микрофону запрещен.';
      };

      // Браузер иногда сам останавливает запись при паузах. Этот перезапуск поддерживает ее.
      recognition.onend = () => {
        if (isRecording) {
          try { recognition.start(); } catch(e) {}
        }
      };
    }

    try {
      recognition.start();
      isRecording = true;
      recordingSeconds = 0;
      recordingTimer = setInterval(() => recordingSeconds++, 1000);
      playClickSound();
    } catch (err) {
      micError = 'Не удалось запустить микрофон.';
    }
  }

  function stopRecording(sendData = true) {
    if (isRecording) {
      isRecording = false;
      if (recordingTimer) clearInterval(recordingTimer);
      if (recognition) {
        try { recognition.stop(); } catch(e) {}
      }
      playClickSound();

      if (sendData) {
        // Вместо мгновенной отправки, открываем редактор
        editableTranscript = (finalTranscript + ' ' + interimTranscript).trim();
        if (editableTranscript) {
          isEditingVoice = true; // Открываем режим редактирования
        } else {
          micError = 'Вы ничего не сказали. Попробуйте еще раз.';
          playErrorSound();
          if (stage === 'decision' && currentIncident) startTimer();
        }
      } else {
        if (stage === 'decision' && currentIncident) startTimer();
      }
    }
  }

  // Функция для итоговой отправки отредактированного текста
  function submitEditedText() {
    isEditingVoice = false;
    handleTextRecorded(editableTranscript);
  }

  async function handleTextRecorded(text: string) {
    const inc = currentIncident;
    isAnalyzingVoice = true; 
    stopTimer();

    // Воспроизводим аудио-филлер на время ожидания ответа ИИ
    let fillerAudio: HTMLAudioElement | null = null;
    if (!trainWorld.isAudioMuted) {
      const fillerNum = Math.floor(Math.random() * 3) + 1;
      fillerAudio = new Audio(`/storage/audio/fillers/filler_${fillerNum}.mp3`);
      fillerAudio.volume = 0.75;
      fillerAudio.play().catch(() => {});
    }

    try {
      // Если инцидента нет, мы передаем ID кресла (например "2A") вместо incident_id!
      const targetId = inc?.incident_id || currentSeat?.id || 'free_talk';
      const res = await trainWorld.resolveVoiceIncident(
        targetId, 
        null, 
        text, 
        String(fullDialogueText), 
        currentStep?.expected_rule || 'Свободное вежливое общение'
      );

      // Глушим филлер, когда получен ответ от сервера
      if (fillerAudio) {
        fillerAudio.pause();
        fillerAudio.currentTime = 0;
      }

      feedbackResult = res?.incident_result || res;
      stage = 'feedback';

      if (feedbackResult?.loyalty_delta >= 0 || feedbackResult?.is_passed) playSuccessSound(); else playErrorSound();

      if (feedbackResult?.passenger_audio_base64 && !trainWorld.isAudioMuted) {
        setTimeout(() => {
          const audio = new Audio(`data:audio/mp3;base64,${feedbackResult.passenger_audio_base64}`);
          audio.volume = 0.9;
          audio.play().catch(e => console.warn("Audio autoplay blocked", e));
        }, 50);
      }

    } catch (e) {
      if (fillerAudio) {
        fillerAudio.pause();
        fillerAudio.currentTime = 0;
      }
      playErrorSound();
    } finally {
      isAnalyzingVoice = false;
    }
  }

  function handleComplete() {
    playClickSound(); resetDialogState();
  }

  onDestroy(resetDialogState);
</script>

<!-- ОСНОВНОЙ КОНТЕЙНЕР ДИАЛОГА -->
<div class="vn-dialogue-box" transition:fly={{ y: 40, duration: 200 }}>
  {@render Header()}
  
  <div
    class="vn-speech-area"
    role="region"
    aria-label="Реплика"
  >
    <p class="speech-quote {currentIncident || stage === 'feedback' ? 'speech-urgent' : 'text-stone-400 not-italic text-sm'}">
      {#if displayedText}
        {displayedText}
      {:else}
        {currentSeat?.isOccupied ? 'Пассажир отдыхает.' : 'Кресло свободно.'}
      {/if}
    </p>
  </div>

  <div class="vn-actions-bar">
    {#if currentIncident || stage === 'feedback'}
      {#if stage === 'decision'}
        {#if isProMode}
          {@render VoiceInterface()}
        {:else}
          {@render ChoicesInterface()}
        {/if}
      {:else if stage === 'learning_card'}
        {@render LearningCardInterface()}
      {:else}
        {@render FeedbackInterface()}
      {/if}
    {:else}
      <!-- СВОБОДНЫЙ ДИАЛОГ (FREE-TALK) С ПАССАЖИРОМ В ЛЮБОЙ МОМЕНТ -->
      {#if currentSeat?.isOccupied && isProMode}
        <div class="flex flex-col w-full gap-2">
          {@render VoiceInterface()}
          <div class="flex gap-2 justify-end pt-1 border-t border-[#3d3831]/50">
            {#if currentSeat.ticketStatus !== 'validated'}
              <button class="action-btn text-emerald-300 text-xs" onclick={() => trainWorld.validateCurrentSeat()}>📲 Проверить (АСКП)</button>
            {/if}
            <button class="action-btn text-stone-400 text-xs" onclick={() => trainWorld.switchView('aisle')}>⬅ В проход</button>
          </div>
        </div>
      {:else}
        <div class="flex gap-2 justify-end">
          {#if currentSeat?.isOccupied && currentSeat.ticketStatus !== 'validated'}
            <button class="action-btn text-emerald-300" onclick={() => trainWorld.validateCurrentSeat()}>📲 Проверить (АСКП)</button>
          {/if}
          <button class="action-btn text-stone-400" onclick={() => trainWorld.switchView('aisle')}>⬅ В проход</button>
        </div>
      {/if}
    {/if}
  </div>
</div>

<!-- ======================= СНИППЕТЫ SVELTE 5 ======================= -->

{#snippet Header()}
  <div class="vn-speaker-bar">
    <div class="flex items-center gap-2 flex-wrap">
      <span class="text-sm font-bold text-[#f5f3ef]">👤 {passengerName} • Место {currentSeat?.id || '—'}</span>
      {#if currentSeat?.passenger?.trait}
        <span class="text-xs px-2 py-0.5 rounded bg-blue-900/30 text-blue-300 border border-blue-500/30">Характер: {currentSeat.passenger.trait}</span>
      {/if}
      <!-- Индикатор режима -->
      <span class="text-[10px] font-mono px-2 py-0.5 rounded border {isProMode ? 'bg-rose-950/60 text-rose-300 border-rose-500/50' : 'bg-emerald-950/60 text-emerald-300 border-emerald-500/50'}">
        {isProMode ? '🔥 PRO (Голос)' : '🎓 Обучение (Кнопки)'}
      </span>
    </div>
    {#if currentIncident && stage === 'decision'}
      <span class="text-sm font-bold px-3 py-0.5 rounded border {timeLeft <= 3 ? 'bg-rose-900/30 text-rose-400 border-rose-500' : 'bg-amber-900/20 text-amber-400 border-amber-500'}">⏱️ {formattedSeconds} сек</span>
    {/if}
  </div>
{/snippet}

{#snippet VoiceInterface()}
  <div class="flex flex-col items-center gap-2.5 py-2 w-full">
    <div class="text-xs text-[#a39e95] text-center w-full">
      {#if micError}
        <span class="text-rose-400 font-bold">{micError}</span>
      {:else if isRecording}
        <div class="flex flex-col gap-2 w-full">
          <div class="text-rose-400 font-bold animate-pulse">Идет распознавание [{formattedRecordTimer}]</div>
          <!-- Окно живого текста -->
          <div class="w-full min-h-[3.5rem] p-2.5 rounded-lg bg-black/50 border border-amber-500/40 text-emerald-300 text-left text-sm italic shadow-inner">
            {finalTranscript} <span class="opacity-60">{interimTranscript}</span>
            {#if !finalTranscript && !interimTranscript}
              <span class="opacity-30">Слушаю вас...</span>
            {/if}
          </div>
        </div>
      {:else if isEditingVoice}
        <!-- РЕЖИМ РЕДАКТИРОВАНИЯ ТЕКСТА ПЕРЕД ОТПРАВКОЙ -->
        <div class="flex flex-col gap-1.5 w-full text-left" in:fade={{ duration: 150 }}>
          <div class="flex justify-between items-center text-[11px] text-amber-400 font-bold">
            <span>✏️ Проверьте и отредактируйте распознанную фразу:</span>
            <span class="text-stone-400 font-normal">Enter не отправляет</span>
          </div>
          <textarea
            bind:value={editableTranscript}
            rows="2"
            class="w-full p-2.5 rounded-lg bg-black/70 border border-amber-500/60 text-white text-sm focus:outline-none focus:border-amber-400 resize-none font-sans"
            placeholder="Что вы сказали пассажиру..."
          ></textarea>
        </div>
      {:else if isAnalyzingVoice}
        <span class="text-amber-400 font-bold">LLM оценивает ваш ответ по регламенту...</span>
      {:else}
        {currentIncident ? 'Нажмите микрофон и ответьте голосом. Речь мгновенно распознается в браузере.' : 'Нажмите микрофон, чтобы заговорить с пассажиром в свободной форме.'}
      {/if}
    </div>
    
    <div class="flex gap-2 w-full justify-center mt-1">
      {#if !isRecording && !isEditingVoice}
        <button onclick={startRecording} disabled={isAnalyzingVoice} class="px-6 py-2.5 rounded-full bg-gradient-to-r from-amber-500 to-amber-600 text-black font-bold text-sm shadow-lg disabled:opacity-50 flex gap-2">
          {isAnalyzingVoice ? '⏳ Ожидайте...' : '🎙️ Начать ответ'}
        </button>
      {:else if isRecording}
        <button onclick={() => stopRecording(false)} class="px-4 py-2.5 rounded-full bg-[#282420] text-stone-300 font-bold text-sm border border-[#3d3831] shadow-lg">
          ✖ Отмена
        </button>
        <button onclick={() => stopRecording(true)} class="flex-1 max-w-[200px] px-6 py-2.5 rounded-full bg-rose-600 text-white font-bold text-sm shadow-[0_0_15px_rgba(225,29,72,0.5)] animate-pulse flex justify-center gap-2">
          ⏹ Завершить
        </button>
      {:else if isEditingVoice}
        <button onclick={() => { isEditingVoice = false; editableTranscript = ''; }} class="px-4 py-2 rounded-full bg-[#282420] text-stone-300 font-bold text-xs border border-[#3d3831] hover:bg-[#3d3831]">
          ✖ Сбросить
        </button>
        <button onclick={submitEditedText} class="px-6 py-2 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-[0_0_15px_rgba(16,185,129,0.4)] flex items-center gap-1.5">
          🚀 Отправить ИИ
        </button>
      {/if}
    </div>
  </div>
{/snippet}

{#snippet ChoicesInterface()}
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
    {#each dynamicOptions as opt, idx}
      <button onclick={() => executeOption(opt)} class="text-left p-2.5 rounded-lg bg-[#201d19] border border-[#3d3831] hover:border-amber-400 hover:bg-[#2b2621] text-xs text-[#f5f3ef] transition-colors flex gap-2">
        <span class="font-bold text-amber-500">[{idx + 1}]</span> <span>{opt.text}</span>
      </button>
    {/each}
  </div>
{/snippet}

{#snippet LearningCardInterface()}
  <div class="flex flex-col gap-2 p-1" in:fade={{ duration: 150 }}>
    <div class="text-xs font-bold text-amber-400 border-b border-[#3d3831] pb-1">💡 Разбор (Без штрафов)</div>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
      {#if selectedOption?.why_correct}
        <div class="bg-emerald-950/40 border border-emerald-500/30 rounded-lg p-2 text-xs text-emerald-200">
          <span class="font-bold block mb-1">✅ Почему это верно:</span>{selectedOption.why_correct}
        </div>
      {/if}
      {#if selectedOption?.what_if_wrong}
        <div class="bg-rose-950/30 border border-rose-500/25 rounded-lg p-2 text-xs text-rose-200">
          <span class="font-bold block mb-1">⚠️ Если ошибиться:</span>{selectedOption.what_if_wrong}
        </div>
      {/if}
    </div>
    <button class="self-end px-4 py-1.5 bg-amber-500 text-black font-bold text-xs rounded" onclick={() => { currentStepId = pendingNextStep!; pendingNextStep = null; stage = 'decision'; timeLeft = currentIncident?.steps?.[currentStepId]?.timer_seconds || 30; startTimer(); }}>Далее ➔</button>
  </div>
{/snippet}

{#snippet FeedbackInterface()}
  <div class="flex flex-col gap-2.5 bg-[#1a1816] border border-[#4a433a] rounded-lg p-3" in:fade={{ duration: 150 }}>
    <div class="flex justify-between items-center border-b border-[#3d3831] pb-2">
      <div class="flex items-center gap-2">
        <span class="px-2 py-1 rounded text-xs font-bold {isTimeout || feedbackResult?.is_passed === false ? 'bg-rose-900/50 text-rose-400 border border-rose-500' : 'bg-emerald-900/50 text-emerald-400 border border-emerald-500'}">
          {isTimeout ? '⏱️ Время вышло' : feedbackResult?.is_passed === false ? '❌ Ошибка' : '✅ Решено'}
        </span>
        <span class="text-xs font-bold text-white">{feedbackResult?.feedback_title || ''}</span>
      </div>
      {#if feedbackResult && feedbackResult.loyalty_delta !== undefined}
        <div class="text-xs font-mono font-bold flex gap-2">
          <span class="text-amber-400">Лояльность: {feedbackResult.loyalty_delta > 0 ? '+' : ''}{feedbackResult.loyalty_delta}</span>
          <span class="text-emerald-400">Безопасность: {feedbackResult.safety_delta > 0 ? '+' : ''}{feedbackResult.safety_delta}</span>
        </div>
      {/if}
    </div>

    <!-- Реплика пассажира (ответ ИИ) -->
    {#if feedbackResult?.passenger_reply}
      <div class="bg-amber-950/40 p-2.5 rounded-lg border border-amber-500/40 text-xs text-amber-100 flex items-start gap-2 shadow-inner">
        <span class="text-base leading-none">💬</span>
        <div class="flex-1">
          <strong class="text-amber-400 block mb-0.5">Ответ пассажира:</strong>
          <span class="italic font-medium">«{feedbackResult.passenger_reply.replace(/^[«"]|[»"]$/g, '')}»</span>
        </div>
      </div>
    {/if}

    {#if feedbackResult?.transcription}
      <div class="bg-black/30 p-2 rounded border border-[#3d3831] text-[11px] text-stone-400">
        <strong class="text-stone-300">Ваши слова:</strong> {feedbackResult.transcription}
      </div>
    {/if}

    <p class="text-xs text-[#a39e95] leading-relaxed pt-0.5">
      <strong class="text-amber-300 block mb-0.5">Разбор инструктора:</strong>
      {feedbackResult?.feedback || 'Анализ...'}
    </p>

    <button class="self-end px-5 py-2 mt-1 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 text-stone-950 font-bold text-xs rounded-lg shadow-md" onclick={handleComplete} disabled={!feedbackResult}>
      {currentIncident ? 'Завершить инцидент ➔' : 'Продолжить диалог ➔'}
    </button>
  </div>
{/snippet}

<style>
  .vn-dialogue-box {
    width: 100%; z-index: 30; pointer-events: auto;
    background: rgba(20, 18, 16, 0.95); backdrop-filter: blur(12px);
    border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 1rem;
    padding: 0.75rem 1.25rem; box-shadow: 0 10px 30px rgba(0,0,0,0.7);
    display: flex; flex-direction: column; gap: 0.5rem; max-height: 48vh;
  }
  .vn-speaker-bar { display: flex; justify-content: space-between; border-bottom: 1px solid rgba(61, 56, 49, 0.5); padding-bottom: 0.4rem; }
  .vn-speech-area { background: rgba(26, 24, 22, 0.45); border: 1px solid rgba(61, 56, 49, 0.35); border-radius: 0.5rem; padding: 0.5rem; min-height: 2.5rem; }
  .speech-quote { font-style: italic; color: #f5f3ef; font-size: 0.875rem; margin: 0; }
  .action-btn { padding: 0.45rem 0.85rem; border-radius: 0.5rem; font-size: 0.8125rem; font-weight: 600; background: #201d19; border: 1px solid #3d3831; cursor: pointer; transition: 0.2s; }
  .action-btn:hover { background: #2b2621; border-color: #f59e0b; }
</style>
