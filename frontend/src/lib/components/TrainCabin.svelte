<script lang="ts">
  import { fly, fade } from 'svelte/transition';
  import { trainWorld } from '../stores/trainWorld.svelte';
  import ConductorDialogue from './ConductorDialogue.svelte';
  import CeilingDisplay from './CeilingDisplay.svelte';
  import SeatMapModal from './SeatMapModal.svelte';
  import ShiftDebriefModal from './ShiftDebriefModal.svelte';
  import { playCallBell, playClickSound, playSuccessSound } from '../utils/audio';

  let isSeatMapOpen = $state<boolean>(false);
  let isResetConfirmOpen = $state<boolean>(false);
  let isDebriefOpen = $state<boolean>(false);

  let selectedSeat = $derived(trainWorld.selectedSeat);
  let callingSeat = $derived(
    trainWorld.seats.find(
      (s) =>
        s.activeIncident != null &&
        (typeof s.activeIncident === 'string' || s.activeIncident.phase !== 'passive')
    )
  );
  const isTripFinished = $derived(
    trainWorld.currentKm >= 678.5 || trainWorld.timeSeconds >= 58500
  );

  function getSeatCoords(seatId: string) {
    const row = parseInt(seatId.slice(0, -1)) || 2;
    const letter = seatId.slice(-1);
    const isLeft = letter === 'A' || letter === 'B';

    // Ряд 1 - ближе к проводнику (низ экрана), Ряд 12 - вдалеке у двери
    const depth = Math.min(1, Math.max(0, (row - 1) / 11));

    // По вертикали: ряд 1 на 62%, ряд 12 на 34%
    const top = 62 - depth * 28;
    // По горизонтали: левая сторона сходится к центру (18% -> 43%), правая (82% -> 57%)
    const left = isLeft ? 18 + depth * 25 : 82 - depth * 25;
    const scale = 1.05 - depth * 0.4;

    return { top: `${top}%`, left: `${left}%`, scale, isLeft };
  }

  function handleCallClick(seatId?: string) {
    playCallBell();
    if (seatId) {
      trainWorld.inspectSeat(seatId);
    } else {
      const callingSeat = trainWorld.seats.find((s) => s.activeIncident != null);
      if (callingSeat) {
        trainWorld.inspectSeat(callingSeat.id);
      }
    }
  }

  function handleBackToAisle() {
    playClickSound();
    trainWorld.switchView('aisle');
  }

  function handlePrevSeat() {
    playClickSound();
    trainWorld.prevOccupiedSeat();
    if (trainWorld.selectedSeat) {
      trainWorld.inspectSeat(trainWorld.selectedSeat.id);
    }
  }

  function handleNextSeat() {
    playClickSound();
    trainWorld.nextOccupiedSeat();
    if (trainWorld.selectedSeat) {
      trainWorld.inspectSeat(trainWorld.selectedSeat.id);
    }
  }

  function handleOpenSeatMap() {
    playClickSound();
    isSeatMapOpen = true;
  }

  async function handleConfirmNewTrip() {
    playSuccessSound();
    isResetConfirmOpen = false;
    await trainWorld.startNewTrip();
  }

  let scrollAreaEl = $state<HTMLElement | null>(null);

  function centerScroll(smooth = true) {
    if (!scrollAreaEl) return;
    const maxScroll = scrollAreaEl.scrollWidth - scrollAreaEl.clientWidth;
    if (maxScroll <= 0) return;

    let targetLeft = maxScroll / 2;

    if (trainWorld.currentView === 'seat') {
      const letter = selectedSeat?.id.slice(-1);
      if (letter === 'A' || letter === 'B') {
        targetLeft = maxScroll * 0.22;
      } else if (letter === 'C' || letter === 'D') {
        targetLeft = maxScroll * 0.78;
      } else {
        targetLeft = maxScroll * 0.5;
      }
    } else if (trainWorld.currentView === 'aisle' && callingSeat) {
      const letter = callingSeat.id.slice(-1);
      if (letter === 'A' || letter === 'B') {
        targetLeft = maxScroll * 0.25;
      } else if (letter === 'C' || letter === 'D') {
        targetLeft = maxScroll * 0.75;
      }
    }

    scrollAreaEl.scrollTo({
      left: targetLeft,
      behavior: smooth ? 'smooth' : 'auto'
    });
  }

  $effect(() => {
    // Реактивно отслеживаем переключение режима и выбранное место
    const view = trainWorld.currentView;
    const seatId = selectedSeat?.id;
    const callId = callingSeat?.id;

    const timer = setTimeout(() => {
      centerScroll(true);
    }, 120);

    return () => clearTimeout(timer);
  });

  function handleWindowResize() {
    centerScroll(false);
  }
</script>

<!-- Контейнер экрана -->
<svelte:window onresize={handleWindowResize} />

<div class="cabin-viewport">
  <!-- Системный плавающий тост событий станции / оповещений проводника -->
  {#if trainWorld.stationToast}
    <div class="station-toast-overlay" transition:fly={{ y: -20, duration: 250 }}>
      <div class="toast-card">
        <div class="toast-title">{trainWorld.stationToast.title}</div>
        <div class="toast-subtitle">{trainWorld.stationToast.subtitle}</div>
      </div>
    </div>
  {/if}

  <!-- Верхний фиксированный HUD-слой (не зависит от горизонтального скролла) -->
  <div class="hud-top-bar">
    {#if trainWorld.currentView === 'aisle'}
      <!-- Статус-баннер текущей фазы смены проводника -->
      <div class="aisle-phase-banner">
        {#if trainWorld.shiftPhase === 'initial_round'}
          <div class="phase-banner-content phase-round">
            <span class="phase-text">
              📋 <strong>Ожидание отправления (Москва)</strong> • АСКП: {trainWorld.validatedCount}/{trainWorld.occupiedSeatsCount}
            </span>
          </div>
        {:else if trainWorld.shiftPhase === 'cruise'}
          <div class="phase-banner-content phase-cruise">
            <span class="phase-pulse-dot"></span>
            <span class="phase-text">
              ⚡ <strong>В пути ({Math.round(trainWorld.speed)} км/ч)</strong>
            </span>
          </div>
        {:else if trainWorld.shiftPhase === 'station_warning' || trainWorld.shiftPhase === 'tver_warning'}
          <div class="phase-banner-content phase-warning">
            <span class="phase-text">
              ⚠️ <strong>{trainWorld.nextStation?.label || 'ст. Тверь'} через 10 мин</strong> • На выход: {trainWorld.nextStationExitingPassengers.length} пасс. ({trainWorld.nextStationRemindedCount}/{trainWorld.nextStationExitingPassengers.length})
            </span>
          </div>
        {:else}
          <div class="phase-banner-content phase-arrival">
            <span class="phase-text">
              🏁 <strong>{trainWorld.currentKm >= 679 ? 'Санкт-Петербург Главный' : 'Стоянка на станции'}</strong> • {trainWorld.currentKm >= 679 ? 'Рейс № 754 успешно завершен' : 'Посадка/высадка'}
            </span>
          </div>
        {/if}
      </div>

      <!-- Верхний правый блок действий: Схема вагона -->
      <div class="top-actions-cluster">
        <button onclick={handleOpenSeatMap} class="seat-map-trigger-btn" title="Открыть интерактивную схему мест вагона">
          <span class="trigger-icon">📋</span>
          <span class="trigger-text">Схема ({trainWorld.occupiedSeatsCount}/48)</span>
          {#if trainWorld.alertSeatsCount > 0}
            <span class="trigger-alert-badge">
              <span class="trigger-alert-ping"></span>
              {trainWorld.alertSeatsCount}
            </span>
          {/if}
        </button>
      </div>
    {:else}
      <!-- Верхняя панель быстрого обхода пассажиров -->
      <div class="seat-top-bar">
        <div class="seat-stepper-mini">
          <button onclick={handlePrevSeat} class="stepper-mini-btn" title="Предыдущий занятый пассажир">
            ◀ Пред
          </button>
          <button onclick={handleOpenSeatMap} class="stepper-mini-seat" title="Открыть карту мест">
            💺 Место {selectedSeat?.id || '—'}
          </button>
          <button onclick={handleNextSeat} class="stepper-mini-btn" title="Следующий занятый пассажир">
            След ▶
          </button>
        </div>
      </div>
    {/if}
  </div>

  <!-- ОСНОВНАЯ ЗОНА СЦЕНЫ (2.5D Салон с горизонтальным скроллом) -->
  <div class="scene-scroll-area hide-scrollbar" bind:this={scrollAreaEl}>
    {#if trainWorld.currentView === 'aisle'}
      <!-- Общий вид вагона (патрулирование) -->
      <div
        class="scene-container aisle-scene"
        class:high-speed-shake={trainWorld.speed > 250 && !trainWorld.isPaused}
        class:ambient-sway={trainWorld.speed > 5 && !trainWorld.isPaused}
      >
        <!-- ================= ЛЕВЫЕ ОКНА ================= -->
        <div class="window-viewport left-viewport">
          <!-- Небо -->
          <div
            class="parallax-layer sky-layer"
            class:is-moving={trainWorld.speed > 5 && !trainWorld.isPaused}
          ></div>
          <!-- Земля -->
          <div
            class="parallax-layer ground-layer"
            class:is-moving={trainWorld.speed > 5 && !trainWorld.isPaused}
          ></div>
        </div>

        <!-- ================= ПРАВЫЕ ОКНА ================= -->
        <div class="window-viewport right-viewport">
          <!-- Небо -->
          <div
            class="parallax-layer sky-layer"
            class:is-moving={trainWorld.speed > 5 && !trainWorld.isPaused}
          ></div>
          <!-- Земля -->
          <div
            class="parallax-layer ground-layer"
            class:is-moving={trainWorld.speed > 5 && !trainWorld.isPaused}
          ></div>
        </div>

        <!-- СЛОЙ 1В: Платформа станции (плавно проявляется при остановке) -->
        <div
          class="station-platform-layer"
          class:platform-visible={trainWorld.speed < 5 && trainWorld.movementStatus.includes('Стоянка')}
        ></div>

        <!-- СЛОЙ 2: Салон с вырезанными окнами (задает геометрию контейнера) -->
        <img
          src="/assets/cabin_aisle_transparent.png"
          alt="Вагон"
          class="base-image cabin-overlay"
        />

        <CeilingDisplay />

        <!-- === МИНИ-ИГРА: ПРИЕМКА ВАГОНА (ПЕРЕД ОТПРАВЛЕНИЕМ) === -->
        {#if trainWorld.shiftPhase === 'initial_round'}
          {#if !trainWorld.preTripChecks.fireExtinguisher}
            <button class="interactive-hotspot" style="top: 55%; left: 10%;" onclick={() => { trainWorld.preTripChecks.fireExtinguisher = true; playSuccessSound(); trainWorld.showToast('Приемка', 'Огнетушитель проверен (пломба на месте).'); }}>
              <span class="hotspot-ping"></span>🧯
            </button>
          {/if}
          {#if !trainWorld.preTripChecks.climate}
            <button class="interactive-hotspot" style="top: 30%; left: 90%;" onclick={() => { trainWorld.preTripChecks.climate = true; playSuccessSound(); trainWorld.showToast('Приемка', 'Щит управления: климат в норме (+22°C).'); }}>
              <span class="hotspot-ping"></span>🌡️
            </button>
          {/if}
          {#if !trainWorld.preTripChecks.toilet}
            <button class="interactive-hotspot" style="top: 45%; left: 45%; transform: scale(0.6);" onclick={() => { trainWorld.preTripChecks.toilet = true; playSuccessSound(); trainWorld.showToast('Приемка', 'Санузел проверен: вода и бумага в наличии.'); }}>
              <span class="hotspot-ping"></span>🚻
            </button>
          {/if}
        {/if}

        <!-- === МИНИ-ИГРА: СДАЧА ВАГОНА И УБОРКА (ПРИБЫТИЕ) === -->
        {#if trainWorld.shiftPhase === 'arrival' || isTripFinished}
          {#each trainWorld.postTripItems as item}
            {#if !item.isFound}
              <button class="interactive-hotspot" style="top: {item.top}; left: {item.left};" onclick={() => { item.isFound = true; playSuccessSound(); trainWorld.showToast('Обход вагона', item.type === 'lost' ? 'Найдена забытая вещь! Передано ЛНП.' : 'Мусор убран.'); }}>
                <span class="hotspot-ping"></span>{item.icon}
              </button>
            {/if}
          {/each}
        {/if}

        <!-- Индикатор активного вызова проводника и пространственная подсветка -->
        {#if callingSeat}
          {@const pos = getSeatCoords(callingSeat.id)}

          <!-- Пульсирующее красное световое пятно над рядом (Ambient Alert Halo) -->
          <div
            class="absolute pointer-events-none z-20 w-32 h-32 rounded-full -translate-x-1/2 -translate-y-1/2 bg-rose-600/30 blur-2xl animate-pulse"
            style="top: {pos.top}; left: {pos.left};"
          ></div>

          <!-- Динамический бейдж вызова точно над креслом в перспективе -->
          <button
            onclick={() => handleCallClick(callingSeat.id)}
            class="aisle-call-badge"
            style="top: {pos.top}; left: {pos.left}; transform: translate(-50%, -50%) scale({pos.scale});"
            title="Подойти к месту {callingSeat.id}"
          >
            <span class="call-ping"></span>
            <!-- Добавлен таймер реакции! -->
            🛎️ Место {callingSeat.id} • Ожидание: {Math.ceil(trainWorld.reactionTimeLeft)} сек ➔
          </button>
        {/if}

        <!-- Пассивные пассажиры в проходе (скрытый 👁️, нетрезвый 🍺, спящий 💤) -->
        {#each trainWorld.seats.filter(s => s.isOccupied && ((s.activeIncident && typeof s.activeIncident === 'object' && s.activeIncident.phase === 'passive') || s.condition === 'drunk' || s.condition === 'sleeping')) as passiveSeat}
          {#if !callingSeat || callingSeat.id !== passiveSeat.id}
            {@const ppos = getSeatCoords(passiveSeat.id)}
            <button
              onclick={() => handleCallClick(passiveSeat.id)}
              class="aisle-call-badge !bg-stone-900/90 !border-amber-500/60 hover:!bg-stone-800 text-amber-200"
              style="top: {ppos.top}; left: {ppos.left}; transform: translate(-50%, -50%) scale({ppos.scale * 0.85});"
              title="Подойти к месту {passiveSeat.id}"
            >
              <span>
                {#if passiveSeat.activeIncident && typeof passiveSeat.activeIncident === 'object' && passiveSeat.activeIncident.phase === 'passive'}
                  👁️ Место {passiveSeat.id}
                {:else if passiveSeat.condition === 'drunk'}
                  🍺 Место {passiveSeat.id}
                {:else}
                  💤 Место {passiveSeat.id}
                {/if}
              </span>
            </button>
          {/if}
        {/each}
      </div>
    {:else}
      <!-- Вид кресла с пассажиром (диалог / осмотр) -->
      <div
        class="scene-container seat-scene"
        class:ambient-sway={trainWorld.speed > 5 && !trainWorld.isPaused}
      >
        <!-- 1. Базовый фон (задает правильный размер без обрезки) -->
        <img src="/assets/seat_bg.png" alt="Салон" class="base-image" />

        <!-- 2. Пассажир (динамический спрайт) -->
        {#if selectedSeat?.isOccupied && selectedSeat?.passenger}
          {@const p = selectedSeat.passenger}
          <img
            src={trainWorld.currentPassengerSprite || p.sprite_url}
            alt={p.full_name}
            class="passenger-overlay"
            onerror={(e) => {
              const target = e.currentTarget as HTMLImageElement;
              target.src = `/assets/passengers/${p.archetype_id}/neutral.png`;
            }}
          />
        {:else if trainWorld.passengerMood !== 'empty'}
          <img
            src={trainWorld.passengerMood === 'calm'
              ? '/assets/passenger_calm.png'
              : '/assets/passenger_annoyed.png'}
            alt="Пассажир"
            class="passenger-overlay"
          />
        {/if}
      </div>
    {/if}
  </div>

  <!-- РАЗДЕЛЕННЫЙ НИЖНИЙ БЛОК ДЕЙСТВИЙ (В проходе — шкала и кнопки, в кресле — диалог) -->
  {#if trainWorld.currentView === 'aisle'}
    <div class="bottom-ui-panel">
      <!-- ЕДИНАЯ КНОПКА УПРАВЛЕНИЯ РЕЙСОМ -->
      <div class="pointer-events-auto">
        {#if isTripFinished}
          <button 
            onclick={() => { isDebriefOpen = true; }} 
            disabled={!trainWorld.isPostTripDone}
            class="px-8 py-3 bg-gradient-to-r from-emerald-600 via-emerald-500 to-teal-400 hover:from-emerald-500 text-white font-extrabold rounded-full shadow-[0_0_25px_rgba(16,185,129,0.5)] transition-all hover:scale-105 flex items-center gap-2 cursor-pointer border border-emerald-300 text-sm tracking-wide disabled:opacity-50 disabled:grayscale disabled:hover:scale-100 disabled:animate-none {trainWorld.isPostTripDone ? 'animate-bounce' : ''}"
          >
            <span>{trainWorld.isPostTripDone ? '🏁 Завершить смену и подвести итоги ➔' : '🧹 Проведите осмотр и уборку вагона...'}</span>
          </button>
        {:else if trainWorld.alertSeatsCount > 0}
          {@const incSeat = trainWorld.seats.find((s) => s.activeIncident != null)}
          <button 
            onclick={() => handleCallClick(incSeat?.id)} 
            class="px-6 py-2.5 bg-gradient-to-r from-rose-600 to-amber-500 text-white font-bold rounded-full shadow-[0_0_20px_rgba(244,63,94,0.6)] animate-pulse flex items-center gap-2 cursor-pointer border border-rose-300"
          >
            <span>🚨 Место {incSeat?.id}: требуется решение проводника ➔</span>
          </button>
        {:else if trainWorld.shiftPhase === 'initial_round'}
          <button 
            onclick={() => { playSuccessSound(); trainWorld.startCruisePhase(); }} 
            disabled={!trainWorld.isPreTripDone}
            class="px-6 py-2.5 bg-gradient-to-r from-amber-600 to-yellow-500 hover:from-amber-500 hover:to-yellow-400 text-stone-950 font-bold rounded-full shadow-[0_4px_20px_rgba(245,158,11,0.4)] transition-all hover:scale-105 flex items-center gap-2 cursor-pointer disabled:opacity-50 disabled:grayscale disabled:hover:scale-100"
          >
            <span>{trainWorld.isPreTripDone ? '🚀 Отправиться в рейс (14:00) ➔' : '🔍 Проведите приемку вагона перед рейсом...'}</span>
          </button>
        {:else if trainWorld.shiftPhase === 'cruise'}
          <button onclick={() => { playClickSound(); trainWorld.skipToNextEvent(); }} class="px-6 py-2.5 bg-gradient-to-r from-cyan-600 to-teal-500 hover:from-cyan-500 hover:to-teal-400 text-white font-bold rounded-full shadow-[0_4px_20px_rgba(6,182,212,0.4)] transition-all hover:scale-105 flex items-center gap-2 cursor-pointer">
            <span>⏩ Промотать до события ➔</span>
          </button>
        {:else if trainWorld.shiftPhase === 'station_warning' || trainWorld.shiftPhase === 'tver_warning'}
          <button onclick={() => { playClickSound(); trainWorld.skipToNextEvent(); }} class="px-6 py-2.5 bg-gradient-to-r from-rose-600 to-orange-500 hover:from-rose-500 hover:to-orange-400 text-white font-bold rounded-full shadow-[0_4px_20px_rgba(225,29,72,0.4)] transition-all hover:scale-105 flex items-center gap-2 cursor-pointer">
            <span>🚉 Перейти к прибытию ➔</span>
          </button>
        {:else if trainWorld.shiftPhase === 'arrival'}
          <button onclick={() => { playSuccessSound(); trainWorld.startCruisePhase(); }} class="px-6 py-2.5 bg-gradient-to-r from-amber-600 to-yellow-500 hover:from-amber-500 hover:to-yellow-400 text-stone-950 font-bold rounded-full shadow-[0_4px_20px_rgba(245,158,11,0.4)] transition-all hover:scale-105 flex items-center gap-2 cursor-pointer">
            <span>⏩ Отправление дальше ➔</span>
          </button>
        {/if}
      </div>

      <!-- Шкала маршрута -->
      <div class="pointer-events-auto w-full bg-[#141210]/95 backdrop-blur-md border border-[#3d3831] rounded-2xl p-3 sm:p-4 shadow-2xl flex flex-col gap-2">
        <div class="flex justify-between items-center text-[11px] font-mono text-[#a39e95] uppercase font-semibold">
          <!-- Динамическое текущее время слева -->
          <span class="text-[#f5f3ef] bg-[#282420] px-2 py-0.5 rounded border border-[#3d3831]">🕒 {trainWorld.formattedTime}</span>
          
          <div class="text-center flex flex-col items-center">
            <span class="text-amber-400 text-xs">След: {trainWorld.nextStation?.label || 'Санкт-Петербург Главный'}</span>
            <span class="text-[10px] opacity-70">Прибытие: {trainWorld.nextStation?.plannedTime || '16:15'}</span>
          </div>
          
          <span>С-Петербург (16:15)</span>
        </div>
        <div class="relative w-full h-1.5 bg-[#2d2924] rounded-full mt-1">
          <div class="absolute top-0 left-0 h-full bg-amber-500 rounded-full transition-all duration-1000 ease-out" style="width: {trainWorld.progressPercent}%"></div>
          <div class="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-amber-500 rounded-full shadow-[0_0_10px_rgba(245,158,11,0.8)] transition-all duration-1000 ease-out" style="left: {trainWorld.progressPercent}%"></div>
        </div>
      </div>
    </div>
  {:else}
    <div class="dialogue-wrapper">
      <ConductorDialogue />
    </div>
  {/if}

  <!-- Модальное окно интерактивной схемы мест -->
  <SeatMapModal isOpen={isSeatMapOpen} onClose={() => { isSeatMapOpen = false; }} />
  <ShiftDebriefModal isOpen={isDebriefOpen} onClose={() => { isDebriefOpen = false; }} />

  <!-- Модальное окно подтверждения перезапуска рейса -->
  {#if isResetConfirmOpen}
    <div
      class="confirm-modal-backdrop"
      role="presentation"
      onclick={() => (isResetConfirmOpen = false)}
      onkeydown={(e) => { if (e.key === 'Escape') isResetConfirmOpen = false; }}
    >
      <div
        class="confirm-modal-box"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-trip-title"
        tabindex="-1"
        onclick={(e) => e.stopPropagation()}
        onkeydown={(e) => e.stopPropagation()}
      >
        <div id="confirm-trip-title" class="confirm-title">🔄 Начать новую поездку?</div>
        <div class="confirm-desc">
          Текущий рейс поезда «Белый кречет» будет перезапущен. Время вернется на 14:00 (Москва), вагон заполнится новым случайным пулом пассажиров (13–18 чел.).
        </div>
        <div class="confirm-actions">
          <button class="confirm-btn-cancel" onclick={() => (isResetConfirmOpen = false)}>
            Отмена
          </button>
          <button class="confirm-btn-ok" onclick={handleConfirmNewTrip}>
            Начать заново
          </button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Оверлей кинематографичного фазового перехода (монтажная склейка) -->
  {#if trainWorld.isPhaseTransitioning}
    <div 
      transition:fade={{ duration: 600 }}
      class="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-[#050505] text-amber-400"
    >
      <div class="text-4xl mb-6">🚄</div>
      <h2 class="text-2xl font-bold tracking-widest uppercase text-white mb-4">В пути...</h2>
      <p class="text-xl text-[#a39e95] font-mono">
        {trainWorld.timeSkippedText}
      </p>
    </div>
  {/if}
</div>

<style>
  .cabin-viewport {
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background-color: #0f0e0d;
  }

  @media (min-width: 768px) {
    .cabin-viewport {
      display: flex;
      flex-direction: row;
      align-items: center;
      justify-content: center;
      padding: 0.5rem;
    }
  }

  /* HUD Top Bar */
  .hud-top-bar {
    position: absolute;
    top: 0.75rem;
    left: 0.75rem;
    right: 0.75rem;
    z-index: 35;
    display: flex;
    align-items: center;
    justify-content: space-between;
    pointer-events: none;
  }

  .hud-top-bar > * {
    pointer-events: auto;
  }

  @media (min-width: 768px) {
    .hud-top-bar {
      top: 1.25rem;
      left: 1.5rem;
      right: 1.5rem;
      max-width: 96vw;
      margin: 0 auto;
    }
  }

  /* Scroll Area for 2.5D Scene */
  .scene-scroll-area {
    flex: 1 1 0%;
    min-height: 0;
    width: 100%;
    overflow-x: auto;
    overflow-y: hidden;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    touch-action: pan-x;
    -webkit-overflow-scrolling: touch;
  }

  @media (min-width: 768px) {
    .scene-scroll-area {
      flex: none;
      width: auto;
      height: auto;
      overflow: visible;
      justify-content: center;
    }
  }

  /* Hide scrollbars */
  .hide-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
  .hide-scrollbar::-webkit-scrollbar {
    display: none;
  }

  /* Scene Container */
  .scene-container {
    position: relative;
    display: inline-block;
    max-width: 96vw;
    max-height: 84vh;
    border-radius: 1rem;
    overflow: hidden;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8);
    background-color: #000;
  }

  .base-image {
    display: block;
    max-height: 84vh;
    max-width: 96vw;
    width: auto;
    height: auto;
    object-fit: contain;
    user-select: none;
  }

  .passenger-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: contain;
    pointer-events: none;
    user-select: none;
  }

  @media (max-width: 767px) {
    .scene-container {
      height: 100%;
      border-radius: 0;
      max-width: none;
      max-height: none;
      flex-shrink: 0;
      box-shadow: none;
    }

    .scene-container.aisle-scene {
      width: 140vw;
    }

    .scene-container.seat-scene {
      width: 180vw;
      transition: width 0.5s ease-in-out;
    }

    .base-image {
      width: 100%;
      height: 100%;
      max-width: none;
      max-height: none;
      object-fit: cover;
      object-position: center;
    }

    .passenger-overlay {
      width: 100%;
      height: 100%;
      max-width: none;
      max-height: none;
      object-fit: cover;
      object-position: center;
    }

    .ambient-sway {
      animation: swayPan 14s ease-in-out infinite alternate;
      will-change: transform;
    }

    .scene-scroll-area:active .ambient-sway {
      animation-play-state: paused;
    }

    @keyframes swayPan {
      0% {
        transform: translateX(-1.2%);
      }
      100% {
        transform: translateX(1.2%);
      }
    }
  }

  /* Bottom UI Panel (Aisle view) */
  .bottom-ui-panel {
    position: absolute;
    bottom: 1.5rem;
    left: 50%;
    transform: translateX(-50%);
    width: 91.666667%;
    max-width: 48rem;
    z-index: 30;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    pointer-events: none;
  }

  @media (max-width: 767px) {
    .bottom-ui-panel {
      position: relative;
      bottom: auto;
      left: auto;
      transform: none;
      width: 100%;
      max-width: none;
      flex-shrink: 0;
      z-index: 30;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem 1rem 1rem;
      background: #0f0e0d;
      border-top: 1px solid #262320;
      pointer-events: auto;
    }
  }

  /* Dialogue Wrapper (Seat view) */
  .dialogue-wrapper {
    position: absolute;
    bottom: 1.5rem;
    left: 50%;
    transform: translateX(-50%);
    width: 91.666667%;
    max-width: 54rem;
    z-index: 30;
    pointer-events: none;
  }

  @media (max-width: 767px) {
    .dialogue-wrapper {
      position: relative;
      bottom: auto;
      left: auto;
      transform: none;
      width: 100%;
      max-width: none;
      flex-shrink: 0;
      z-index: 30;
      pointer-events: auto;
      background: #0f0e0d;
      border-top: 1px solid #262320;
      max-height: 48vh;
      overflow-y: auto;
    }
  }



  .aisle-call-badge {
    position: absolute;
    z-index: 25;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.875rem;
    border-radius: 0.75rem;
    background: linear-gradient(135deg, rgba(244, 63, 94, 0.95), rgba(225, 29, 72, 0.95));
    border: 2px solid rgba(254, 205, 211, 0.9);
    color: #ffffff;
    font-size: 0.8125rem;
    box-shadow: 0 10px 25px -3px rgba(225, 29, 72, 0.6), 0 0 15px rgba(244, 63, 94, 0.5);
    cursor: pointer;
    white-space: nowrap;
    transition: filter 0.15s ease, box-shadow 0.15s ease;
  }

  .aisle-call-badge:hover {
    filter: brightness(1.15);
    box-shadow: 0 12px 30px -3px rgba(225, 29, 72, 0.8), 0 0 25px rgba(244, 63, 94, 0.75);
  }

  .call-ping {
    position: absolute;
    top: -4px;
    right: -4px;
    width: 12px;
    height: 12px;
    border-radius: 9999px;
    background-color: #f43f5e;
    animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
  }

  @keyframes ping {
    75%, 100% {
      transform: scale(2);
      opacity: 0;
    }
  }

  /* Баннер фазы смены проводника над проходом */
  .aisle-phase-banner {
    position: relative;
    z-index: 25;
  }

  .phase-banner-content {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.35rem 0.8rem;
    border-radius: 0.625rem;
    background: rgba(20, 18, 16, 0.92);
    backdrop-filter: blur(10px);
    border: 1px solid #3d3831;
    color: #f5f3ef;
    font-size: 0.75rem;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.6);
  }

  .phase-round {
    border-color: rgba(245, 158, 11, 0.4);
  }

  .phase-cruise {
    border-color: rgba(59, 130, 246, 0.4);
    background: rgba(15, 23, 42, 0.92);
  }

  .phase-warning {
    border-color: rgba(245, 158, 11, 0.8);
    background: rgba(45, 30, 15, 0.95);
    box-shadow: 0 0 20px rgba(245, 158, 11, 0.3);
  }

  .phase-arrival {
    border-color: rgba(16, 185, 129, 0.5);
    background: rgba(10, 30, 20, 0.92);
  }

  .phase-pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #3b82f6;
    box-shadow: 0 0 8px #3b82f6;
    animation: pulse 1.5s infinite;
  }

  /* Блок кнопок в правом верхнем углу */
  .top-actions-cluster {
    position: relative;
    z-index: 25;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  @media (max-width: 640px) {
    .phase-banner-content {
      font-size: 0.6875rem;
      padding: 0.25rem 0.5rem;
      gap: 0.4rem;
    }
    .seat-map-trigger-btn {
      font-size: 0.6875rem;
      padding: 0.25rem 0.5rem;
    }
  }

  /* Кнопка открытия схемы вагона */
  .seat-map-trigger-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.45rem 0.85rem;
    border-radius: 0.625rem;
    background: rgba(26, 24, 22, 0.9);
    backdrop-filter: blur(10px);
    border: 1px solid #3d3831;
    color: #f5f3ef;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.6);
    transition: all 0.15s ease;
  }

  .seat-map-trigger-btn:hover {
    background: rgba(40, 36, 32, 0.95);
    border-color: #f59e0b;
    color: #f59e0b;
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.7), 0 0 12px rgba(245, 158, 11, 0.2);
  }

  .trigger-icon {
    font-size: 0.875rem;
  }

  .trigger-alert-badge {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.1rem 0.4rem;
    border-radius: 9999px;
    background: #e11d48;
    color: #ffffff;
    font-size: 0.6875rem;
    font-weight: 700;
    line-height: 1;
  }

  .trigger-alert-ping {
    position: absolute;
    inset: -2px;
    border-radius: 9999px;
    background: #f43f5e;
    opacity: 0.75;
    animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
  }



  /* Плавающий системный тост событий станции */
  .station-toast-overlay {
    position: absolute;
    top: 1.25rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: 50;
    pointer-events: none;
    max-width: 90vw;
  }

  .toast-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    padding: 0.6rem 1.25rem;
    border-radius: 0.75rem;
    background: rgba(20, 18, 16, 0.95);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(245, 158, 11, 0.6);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8), 0 0 18px rgba(245, 158, 11, 0.25);
    text-align: center;
    color: #f5f3ef;
  }

  .toast-title {
    font-size: 0.875rem;
    font-weight: 700;
    color: #f59e0b;
    letter-spacing: 0.02em;
  }

  .toast-subtitle {
    font-size: 0.75rem;
    font-weight: 500;
    color: #d6d3cd;
    line-height: 1.3;
  }

  /* Модальное окно подтверждения */
  .confirm-modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 60;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(6px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }

  .confirm-modal-box {
    width: 100%;
    max-width: 440px;
    background: #1a1816;
    border: 1px solid #4a433a;
    border-radius: 1rem;
    padding: 1.5rem;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.8), 0 0 25px rgba(245, 158, 11, 0.15);
    display: flex;
    flex-direction: column;
    gap: 1rem;
    color: #f5f3ef;
  }

  .confirm-title {
    font-size: 1.125rem;
    font-weight: 700;
    color: #f59e0b;
  }

  .confirm-desc {
    font-size: 0.875rem;
    color: #a8a29e;
    line-height: 1.5;
  }

  .confirm-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    margin-top: 0.5rem;
  }

  .confirm-btn-cancel {
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    background: #282420;
    border: 1px solid #4a433a;
    color: #d6d3cd;
    font-size: 0.8125rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .confirm-btn-cancel:hover {
    background: #342f2a;
    color: #ffffff;
  }

  .confirm-btn-ok {
    padding: 0.5rem 1.1rem;
    border-radius: 0.5rem;
    background: linear-gradient(135deg, #f59e0b, #d97706);
    border: 1px solid #fbbf24;
    color: #0f0e0d;
    font-size: 0.8125rem;
    font-weight: 700;
    cursor: pointer;
    box-shadow: 0 2px 10px rgba(245, 158, 11, 0.3);
    transition: all 0.15s ease;
  }

  .confirm-btn-ok:hover {
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(245, 158, 11, 0.45);
  }

  .seat-top-bar {
    position: relative;
    width: 100%;
    z-index: 25;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
  }

  .seat-top-bar > * {
    pointer-events: auto;
  }

  .seat-stepper-mini {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(20, 18, 16, 0.92);
    backdrop-filter: blur(10px);
    border: 1px solid #3d3831;
    padding: 0.25rem 0.4rem;
    border-radius: 0.625rem;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.6);
  }

  .stepper-mini-btn {
    padding: 0.3rem 0.65rem;
    border-radius: 0.375rem;
    background: #23201c;
    border: 1px solid #3d3831;
    color: #d6d3d1;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .stepper-mini-btn:hover {
    border-color: #f59e0b;
    color: #f59e0b;
    background: #2d2822;
  }

  .stepper-mini-seat {
    padding: 0.3rem 0.65rem;
    border-radius: 0.375rem;
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid rgba(245, 158, 11, 0.4);
    color: #fbbf24;
    font-family: ui-monospace, SFMono-Regular, monospace;
    font-size: 0.75rem;
    font-weight: 700;
    cursor: pointer;
  }

  .stepper-mini-seat:hover {
    background: rgba(245, 158, 11, 0.25);
    border-color: #f59e0b;
  }

  /* Контейнеры левой и правой половины вагона */
  .window-viewport {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 50%;
    z-index: 1;
    overflow: hidden;
    pointer-events: none;
  }

  .left-viewport {
    left: 0;
  }

  /* Правую половину зеркалим, чтобы движение шло вправо и не двоился рисунок */
  .right-viewport {
    right: 0;
    transform: scaleX(-1);
  }

  /* Базовый класс полотна: по умолчанию на паузе (для стоянок) */
  .parallax-layer {
    position: absolute;
    inset: 0;
    background-repeat: repeat-x;
    animation: flowLeft linear infinite;
    animation-play-state: paused; /* Стоит на месте */
  }

  /* Включается в движение только когда поезд едет */
  .parallax-layer.is-moving {
    animation-play-state: running;
  }

  /* 1. СЛОЙ НЕБА: неторопливый цикл 20 секунд */
  .sky-layer {
    z-index: 1;
    background-image: url('/assets/bg_sky.jpg');
    background-size: auto 100%;
    background-position: 0 0;
    animation-duration: 30s; /* Фиксированное плавное скольжение */
  }

  /* 2. СЛОЙ ЗЕМЛИ: комфортный цикл 10 секунд */
  .ground-layer {
    z-index: 2;
    top: 35%; /* Опущено на 5% ниже */
    background-image: url('/assets/bg_bottom.png');
    background-size: auto 100%;
    background-position: 0 bottom;
    animation-duration: 15s; /* Фиксированный спокойный ход без ряби */
  }

  /* Бесконечный сдвиг полотна */
  @keyframes flowLeft {
    from {
      background-position-x: 0;
    }
    to {
      background-position-x: -2000px;
    }
  }

  /* Прозрачный салон поверх пейзажа */
  .cabin-overlay {
    position: relative;
    z-index: 2; /* Поверх пейзажа, но под табло (у табло z-index: 15) */
  }

  /* Легкая микро-вибрация салона на сверхскорости */
  .high-speed-shake {
    animation: cabinShake 0.15s infinite ease-in-out alternate;
  }

  @keyframes cabinShake {
    0% { transform: translateY(0); }
    100% { transform: translateY(0.75px); }
  }

  /* Слой перрона/платформы */
  .station-platform-layer {
    position: absolute;
    inset: 0;
    z-index: 1; /* Поверх бегущего леса, но под салоном */
    background-image: url('/assets/platform_station.jpg');
    background-size: cover;
    background-position: center;
    opacity: 0;
    transition: opacity 1.5s ease-in-out; /* Плавное перетекание за 1.5 сек */
    pointer-events: none;
  }

  .station-platform-layer.platform-visible {
    opacity: 1;
  }

  /* Стили для мини-игр обхода вагона */
  .interactive-hotspot {
    position: absolute;
    z-index: 25;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    background: rgba(20, 18, 16, 0.8);
    border: 2px solid #f59e0b;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 0 15px rgba(245, 158, 11, 0.5);
    transition: all 0.2s ease;
  }

  .interactive-hotspot:hover {
    transform: scale(1.15) !important;
    background: #f59e0b;
  }

  .hotspot-ping {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 2px solid #f59e0b;
    animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
  }
</style>
