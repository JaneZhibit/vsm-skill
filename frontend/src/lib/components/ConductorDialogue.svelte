<script lang="ts">
  import { onDestroy } from 'svelte';
  import { fade, fly, slide } from 'svelte/transition';
  import { trainWorld } from '../stores/trainWorld.svelte';
  import { cabinState } from '../stores/cabinState.svelte';
  import { trainAudio } from '../stores/trainAudio.svelte';
  import { conductorState } from '../stores/conductorState.svelte';
  import type { ActiveIncident } from '../config/cabinConfig';
  import { playSuccessSound, playErrorSound, playClickSound } from '../utils/audio';
  import { voiceRecognition } from '../services/voiceRecognition.svelte';

  type Stage = 'decision' | 'feedback';

  let currentSeat = $derived(cabinState.selectedSeat);
  let activeIncident = $derived(currentSeat?.activeIncident);
  let dialogIncident = $state<ActiveIncident | null>(cabinState.selectedSeat?.activeIncident || null);
  let currentIncident = $derived<ActiveIncident | null>(dialogIncident || activeIncident || null);

  let currentStepId = $state<string>('step_1');
  let currentStep = $derived<any>(currentIncident?.steps?.[currentStepId] || currentIncident || { options: [] });

  let isEditingVoice = $state<boolean>(false);
  let editableTranscript = $state<string>('');

  // Новое состояние для сворачивания панели
  let isCollapsed = $state<boolean>(false);

  // --- ЛОГИКА РЕЖИМОВ ---
  let isProMode = $derived(trainWorld.tripMode === 'pro');

  let stage = $state<Stage>('decision');
  let timeLeft = $state<number>(0);
  let isTimeout = $state<boolean>(false);
  let timerInterval: ReturnType<typeof setInterval> | null = null;
  let feedbackResult = $state<any>(null);
  let isAnalyzingVoice = $state<boolean>(false);

  // --- ДАННЫЕ UI ---
  let formattedSeconds = $derived(Math.ceil(timeLeft).toString().padStart(2, '0'));
  let formattedRecordTimer = $derived(`00:${voiceRecognition.recordingSeconds.toString().padStart(2, '0')}`);
  let passengerName = $derived(currentSeat?.isOccupied ? (currentSeat.passenger?.full_name || 'Пассажир') : 'Свободное место');

  let currentHint = $derived.by(() => {
    const inc = currentIncident as any;
    if (inc?.expected_rule) return inc.expected_rule;
    if (currentStep?.expected_rule) return currentStep.expected_rule;

    const opts = currentStep?.options || inc?.options || [];
    const correctOpt = opts.find((o: any) => (o.result?.loyalty_delta && o.result.loyalty_delta > 0) || o.why_correct);
    if (correctOpt) {
      return correctOpt.expected_rule || correctOpt.why_correct || `Рекомендуемое действие: ${correctOpt.text}`;
    }
    return 'Соблюдайте вежливое общение и стандарты безопасной перевозки пассажиров на ВСМ.';
  });

  let displayedText = $derived.by(() => {
    if (feedbackResult?.passenger_reply) return `«${feedbackResult.passenger_reply.replace(/^[«"]|[»"]$/g, '')}»`;

    const inc = currentIncident;
    if (inc) {
      const rawPrompt = currentStep?.prompt ?? inc?.prompt;
      if (rawPrompt) {
        if (typeof rawPrompt === 'object') {
          const archId = currentSeat?.passenger?.archetype_id || 'male_young';
          const trait = currentSeat?.passenger?.trait || 'polite';
          return rawPrompt[`${archId}_${trait}`] || rawPrompt[trait] || rawPrompt[archId] || rawPrompt['default'] || '';
        }
        return String(rawPrompt);
      }
    }
    return '';
  });

  let currentSeatId = $derived(currentSeat?.id);
  let boundSeatId = cabinState.selectedSeat?.id || '';
  let initializedIncidentId = '';

  $effect(() => {
    if (currentSeatId !== boundSeatId) {
      boundSeatId = currentSeatId || '';
      resetDialogState();
    }

    if (activeIncident && stage === 'decision' && activeIncident.incident_id !== initializedIncidentId) {
      initializedIncidentId = activeIncident.incident_id;
      dialogIncident = activeIncident;
      currentStepId = activeIncident.start_step || 'step_1';
      timeLeft = currentStep?.timer_seconds || activeIncident.timer_seconds || 30;
      trainAudio.setAmbientDucking(true);
      if (currentSeat?.passenger) trainWorld.playPassengerDialog(activeIncident.incident_id, currentSeat.passenger.archetype_id, currentSeat.passenger.trait);
      startTimer();
    }
  });

  function resetDialogState() {
    dialogIncident = null;
    initializedIncidentId = '';
    stopTimer();
    voiceRecognition.reset();
    stage = 'decision';
    currentStepId = 'step_1';
    feedbackResult = null;
    isTimeout = false;
    isEditingVoice = false;
    editableTranscript = '';
    isCollapsed = false;
    trainAudio.setAmbientDucking(false);
  }

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
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
  }

  async function triggerTimeout() {
    if (!currentIncident?.incident_id) return;
    stopTimer();
    voiceRecognition.stop();
    isTimeout = true;
    stage = 'feedback';
    isCollapsed = false;
    playErrorSound();
    feedbackResult = await cabinState.resolveIncident(currentIncident.incident_id, 'opt_timeout');
  }

  function handleStartRecording() { stopTimer(); voiceRecognition.start(); }

  function handleStopRecording(sendData = true) {
    const transcript = voiceRecognition.stop();
    if (sendData) {
      editableTranscript = transcript;
      if (editableTranscript) { isEditingVoice = true; }
      else { playErrorSound(); if (stage === 'decision' && currentIncident) startTimer(); }
    } else {
      if (stage === 'decision' && currentIncident) startTimer();
    }
  }

  function submitEditedText() {
    isEditingVoice = false;
    handleTextRecorded(editableTranscript);
  }

  async function handleTextRecorded(text: string) {
    isAnalyzingVoice = true;
    stopTimer();

    let fillerAudio: HTMLAudioElement | null = null;
    if (!trainAudio.isAudioMuted) {
      fillerAudio = new Audio(`/storage/audio/fillers/filler_${Math.floor(Math.random() * 3) + 1}.mp3`);
      fillerAudio.volume = 0.75;
      fillerAudio.play().catch(() => {});
    }

    try {
      const targetId = currentIncident?.incident_id || currentSeat?.id || 'free_talk';
      const res = await cabinState.resolveVoiceIncident(targetId, null, text, displayedText, currentHint);
      if (fillerAudio) { fillerAudio.pause(); fillerAudio.currentTime = 0; }

      feedbackResult = res?.incident_result || res;
      stage = 'feedback';
      isCollapsed = false; // Разворачиваем, чтобы показать результат

      if (feedbackResult?.loyalty_delta >= 0 || feedbackResult?.is_passed) playSuccessSound(); else playErrorSound();

      if (feedbackResult?.passenger_audio_base64 && !trainAudio.isAudioMuted) {
        setTimeout(() => {
          const audio = new Audio(`data:audio/mp3;base64,${feedbackResult.passenger_audio_base64}`);
          audio.volume = 0.9;
          audio.play().catch(() => {});
        }, 50);
      }
    } catch (e) {
      if (fillerAudio) { fillerAudio.pause(); fillerAudio.currentTime = 0; }
      playErrorSound();
    } finally {
      isAnalyzingVoice = false;
    }
  }

  function handleComplete() { playClickSound(); resetDialogState(); }

  onDestroy(resetDialogState);
</script>

<div class="vn-dialogue-box" transition:fly={{ y: 40, duration: 200 }}>
  <!-- ШАПКА ДИАЛОГА -->
  <div class="vn-speaker-bar flex-col sm:flex-row gap-2">
    <div class="flex items-center gap-2 flex-wrap flex-1">
      <span class="text-sm font-bold text-[#f5f3ef]">👤 Место {currentSeat?.id || '—'}</span>
      {#if currentSeat?.passenger?.trait}
        <span class="text-[10px] px-1.5 py-0.5 rounded bg-blue-900/30 text-blue-300 border border-blue-500/30">{currentSeat.passenger.trait}</span>
      {/if}
      <span class="text-[10px] font-mono px-1.5 py-0.5 rounded border {isProMode ? 'bg-rose-950/60 text-rose-300 border-rose-500/50' : 'bg-indigo-950/60 text-indigo-300 border-indigo-500/50'}">
        {isProMode ? 'PRO' : 'БАЗА'}
      </span>
      {#if currentIncident && stage === 'decision'}
        <span class="text-xs font-bold px-2 py-0.5 rounded border {timeLeft <= 3 ? 'bg-rose-900/30 text-rose-400 border-rose-500 animate-pulse' : 'bg-amber-900/20 text-amber-400 border-amber-500'}">
          ⏱️ {formattedSeconds} с
        </span>
      {/if}
    </div>

    <!-- Кнопки управления окном -->
    <div class="flex items-center gap-1.5 shrink-0 self-end sm:self-auto">
      {#if !currentIncident && currentSeat?.ticketStatus !== 'validated'}
        <button class="px-2 py-1 rounded bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs font-bold" onclick={() => cabinState.validateCurrentSeat()}>📲 АСКП</button>
      {/if}
      <button onclick={() => {playClickSound(); isCollapsed = !isCollapsed;}} class="px-2 py-1 rounded bg-[#282420] text-stone-300 text-xs font-bold border border-[#3d3831] whitespace-nowrap">
        {isCollapsed ? '▲ Развернуть' : '▼ Свернуть'}
      </button>
      <button onclick={() => {playClickSound(); cabinState.switchView('aisle');}} class="px-2 py-1 rounded bg-[#282420] hover:bg-rose-950 hover:text-rose-300 text-stone-300 text-xs font-bold border border-[#3d3831] whitespace-nowrap">
        ⬅ В проход
      </button>
    </div>
  </div>

  <!-- СВОРАЧИВАЕМАЯ ОБЛАСТЬ -->
  {#if !isCollapsed}
    <div class="flex flex-col gap-2 pt-2" transition:slide={{duration: 200}}>
      <div class="vn-speech-area" role="region" aria-label="Реплика">
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
            {@render VoiceInterface()}
          {:else}
            {@render FeedbackInterface()}
          {/if}
        {:else}
          <!-- СВОБОДНЫЙ ДИАЛОГ -->
          {#if currentSeat?.isOccupied}
            {@render VoiceInterface()}
          {/if}
        {/if}
      </div>
    </div>
  {/if}
</div>

{#snippet VoiceInterface()}
  <div class="flex flex-col items-center gap-2 w-full">
    {#if !isProMode && stage === 'decision' && currentHint}
      <div class="w-full p-2 mb-1 bg-indigo-950/40 border border-indigo-500/40 rounded-lg text-indigo-200 text-[11px] sm:text-xs shadow-inner text-left leading-snug" transition:fade={{duration: 200}}>
        <span class="font-bold text-indigo-400 block mb-0.5">💡 Подсказка:</span>
        {currentHint}
      </div>
    {/if}

    <div class="text-xs text-[#a39e95] text-center w-full">
      {#if voiceRecognition.micError}
        <span class="text-rose-400 font-bold">{voiceRecognition.micError}</span>
      {:else if voiceRecognition.isRecording}
        <div class="flex flex-col gap-1.5 w-full">
          <div class="text-rose-400 font-bold animate-pulse text-[11px] sm:text-xs">Слушаю... [{formattedRecordTimer}]</div>
          <div class="w-full min-h-[3rem] p-2 rounded-lg bg-black/50 border border-amber-500/40 text-emerald-300 text-left text-[11px] sm:text-sm italic shadow-inner">
            {voiceRecognition.finalTranscript} <span class="opacity-60">{voiceRecognition.interimTranscript}</span>
          </div>
        </div>
      {:else if isEditingVoice}
        <div class="flex flex-col gap-1 w-full text-left" in:fade={{ duration: 150 }}>
          <span class="text-[10px] text-amber-400 font-bold">✏️ Проверьте текст:</span>
          <textarea bind:value={editableTranscript} rows="2" class="w-full p-2 rounded-lg bg-black/70 border border-amber-500/60 text-white text-xs sm:text-sm focus:outline-none focus:border-amber-400 resize-none"></textarea>
        </div>
      {:else if isAnalyzingVoice}
        <span class="text-amber-400 font-bold text-[11px] sm:text-xs">Анализ ответа LLM...</span>
      {:else}
        <span class="text-[10px] sm:text-xs">{currentIncident ? 'Нажмите микрофон и ответьте.' : 'Нажмите микрофон для беседы.'}</span>
      {/if}
    </div>

    <div class="flex gap-2 w-full justify-center mt-1">
      {#if !voiceRecognition.isRecording && !isEditingVoice}
        <button onclick={handleStartRecording} disabled={isAnalyzingVoice} class="px-5 py-2 sm:py-2.5 rounded-full bg-gradient-to-r from-amber-500 to-amber-600 text-black font-bold text-xs sm:text-sm shadow-lg disabled:opacity-50 flex gap-2">
          {isAnalyzingVoice ? '⏳ Ожидайте...' : '🎙️ Говорить'}
        </button>
      {:else if voiceRecognition.isRecording}
        <button onclick={() => handleStopRecording(false)} class="px-3 py-2 sm:py-2.5 rounded-full bg-[#282420] text-stone-300 font-bold text-xs sm:text-sm border border-[#3d3831] shadow-lg">✖ Отмена</button>
        <button onclick={() => handleStopRecording(true)} class="flex-1 max-w-[160px] sm:max-w-[200px] px-4 py-2 sm:py-2.5 rounded-full bg-rose-600 text-white font-bold text-xs sm:text-sm shadow-[0_0_15px_rgba(225,29,72,0.5)] animate-pulse flex justify-center gap-2">⏹ Завершить</button>
      {:else if isEditingVoice}
        <button onclick={() => { isEditingVoice = false; editableTranscript = ''; }} class="px-3 py-2 rounded-full bg-[#282420] text-stone-300 font-bold text-xs border border-[#3d3831]">✖ Сброс</button>
        <button onclick={submitEditedText} class="px-4 py-2 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-[0_0_15px_rgba(16,185,129,0.4)]">🚀 Отправить</button>
      {/if}
    </div>
  </div>
{/snippet}

{#snippet FeedbackInterface()}
  <div class="flex flex-col gap-2 bg-[#1a1816] border border-[#4a433a] rounded-lg p-2.5" in:fade={{ duration: 150 }}>
    <div class="flex justify-between items-center border-b border-[#3d3831] pb-1.5 flex-wrap gap-1">
      <div class="flex items-center gap-1.5">
        {#if isTimeout || feedbackResult?.dialog_status === 'failed'}
          <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-900/50 text-rose-400 border border-rose-500">❌ Провал</span>
        {:else if feedbackResult?.dialog_status === 'continue'}
          <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-900/50 text-blue-400 border border-blue-500">💬 Диалог</span>
        {:else}
          <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-900/50 text-emerald-400 border border-emerald-500">✅ Решено</span>
        {/if}
        <span class="text-[11px] font-bold text-white truncate max-w-[150px] sm:max-w-none">{feedbackResult?.feedback_title || ''}</span>
      </div>
      {#if feedbackResult && feedbackResult.loyalty_delta !== undefined}
        <div class="text-[10px] font-mono font-bold flex gap-1.5">
          <span class="text-amber-400">🤝 {feedbackResult.loyalty_delta > 0 ? '+' : ''}{feedbackResult.loyalty_delta}</span>
          <span class="text-emerald-400">🛡️ {feedbackResult.safety_delta > 0 ? '+' : ''}{feedbackResult.safety_delta}</span>
        </div>
      {/if}
    </div>
    {#if feedbackResult?.passenger_reply}
      <div class="bg-amber-950/40 p-2 rounded-lg border border-amber-500/40 text-[11px] text-amber-100 flex items-start gap-1.5 shadow-inner">
        <span>💬</span>
        <div class="flex-1">
          <span class="italic font-medium">«{feedbackResult.passenger_reply.replace(/^[«"]|[»"]$/g, '')}»</span>
        </div>
      </div>
    {/if}
    <p class="text-[10px] sm:text-xs text-[#a39e95] leading-snug">
      <strong class="text-amber-300">Анализ:</strong> {feedbackResult?.feedback || 'Оценка...'}
    </p>

    {#if feedbackResult?.dialog_status === 'continue'}
      <button class="self-end px-4 py-1.5 mt-1 bg-blue-600 text-white font-bold text-xs rounded-lg shadow-md" onclick={() => { stage = 'decision'; timeLeft = currentStep?.timer_seconds || 30; startTimer(); }}>
        Ответить ➔
      </button>
    {:else}
      <button class="self-end px-4 py-1.5 mt-1 bg-amber-600 text-stone-950 font-bold text-xs rounded-lg shadow-md" onclick={handleComplete} disabled={!feedbackResult}>
        Завершить ➔
      </button>
    {/if}
  </div>
{/snippet}

<style>
  .vn-dialogue-box {
    width: 100%; z-index: 30; pointer-events: auto;
    background: rgba(20, 18, 16, 0.96); backdrop-filter: blur(12px);
    border: 1px solid rgba(245, 158, 11, 0.5); border-radius: 1rem 1rem 0 0;
    padding: 0.75rem 1rem;
    padding-bottom: max(1rem, env(safe-area-inset-bottom));
    box-shadow: 0 -10px 30px rgba(0,0,0,0.8);
    display: flex; flex-direction: column; gap: 0.25rem;
  }
  @media (min-width: 768px) {
    .vn-dialogue-box { border-radius: 1rem; padding-bottom: 0.75rem; box-shadow: 0 10px 30px rgba(0,0,0,0.7); }
  }
  .vn-speaker-bar { display: flex; justify-content: space-between; border-bottom: 1px solid rgba(61, 56, 49, 0.5); padding-bottom: 0.4rem; }
  .vn-speech-area { background: rgba(26, 24, 22, 0.6); border: 1px solid rgba(61, 56, 49, 0.5); border-radius: 0.5rem; padding: 0.5rem; min-height: 2.5rem; }
  .speech-quote { font-style: italic; color: #f5f3ef; font-size: 0.8125rem; margin: 0; }
  @media (min-width: 768px) { .speech-quote { font-size: 0.875rem; } }
</style>