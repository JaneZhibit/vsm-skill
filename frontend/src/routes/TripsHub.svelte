<script lang="ts">
  import { authStore } from '../lib/stores/authStore.svelte';
  import { trainWorld } from '../lib/stores/trainWorld.svelte';
  import { playClickSound, playSuccessSound, playErrorSound } from '../lib/utils/audio';

  // Активный выбранный модуль (по умолчанию 'service')
  let selectedTrackId = $state<string>('service');

  interface Lesson {
    id: string;
    num: string;
    stationName: string;
    title: string;
    desc: string;
    status: 'completed' | 'unlocked' | 'locked';
    score?: number;
    reward: string;
    duration: string;
    km: string;
    incidentId: string;
  }

  interface Track {
    id: string;
    title: string;
    icon: string;
    lessons: Lesson[];
  }

  // Честная программа обучения: 5 модулей × 3 урока = 15 уроков
  // Статусы выставлены ровно так, чтобы давать ваши 4/15 со скриншота!
  const modules: Track[] = [
    {
      id: 'service',
      title: 'Базовый сервис',
      icon: '🎫',
      lessons: [
        {
          id: 'lesson_service_1',
          num: '1.1',
          stationName: 'ст. Рижская',
          title: 'Самовольная пересадка',
          desc: 'Пассажир без предупреждения пересел на чужое место у окна и не желает возвращаться.',
          status: 'completed',
          score: 100,
          reward: '+25 Регламент',
          duration: '2 мин',
          km: '5 км',
          incidentId: 'inc_wrong_seat_01',
        },
        {
          id: 'lesson_service_2',
          num: '1.2',
          stationName: 'ст. Зеленоград',
          title: 'Чемодан в проходе',
          desc: 'Пассажир заблокировал центральный эвакуационный проход тяжелым чемоданом.',
          status: 'completed',
          score: 95,
          reward: '+25 Безопасность',
          duration: '2 мин',
          km: '41 км',
          incidentId: 'inc_luggage_aisle_01',
        },
        {
          id: 'lesson_service_3',
          num: '1.3',
          stationName: 'ст. Тверь',
          title: 'Посадочный экспресс',
          desc: 'Отработка комплексного послепосадочного обхода и сверки занятости кресел.',
          status: 'unlocked',
          reward: '+30 Сервис',
          duration: '3 мин',
          km: '167 км',
          incidentId: 'inc_wrong_seat_01',
        },
      ],
    },
    {
      id: 'comfort',
      title: 'Микроклимат и быт',
      icon: '🌡️',
      lessons: [
        {
          id: 'lesson_comfort_1',
          num: '2.1',
          stationName: 'ст. Высоково',
          title: 'Сквозняк от кондиционера',
          desc: 'Жалоба на холодный обдув и требование пассажира открыть глухое окно на 400 км/ч.',
          status: 'completed',
          score: 90,
          reward: '+20 Комфорт',
          duration: '2 мин',
          km: '86 км',
          incidentId: 'inc_temp_01',
        },
        {
          id: 'lesson_comfort_2',
          num: '2.2',
          stationName: 'ст. Новая Тверь',
          title: 'Розетка под креслом',
          desc: 'Не подается питание 220V на блок зарядки у кресла первого класса. Ноутбук садится.',
          status: 'unlocked',
          reward: '+25 Сервис',
          duration: '2 мин',
          km: '167 км',
          incidentId: 'inc_broken_socket_01',
        },
        {
          id: 'lesson_comfort_3',
          num: '2.3',
          stationName: 'ст. Торжок',
          title: 'Сервис рациона бистро',
          desc: 'Закончилось блюдо из меню, пассажир требует вызвать шеф-повара и начальника поезда.',
          status: 'locked',
          reward: '+25 Сервис',
          duration: '3 мин',
          km: '225 км',
          incidentId: 'inc_temp_01',
        },
      ],
    },
    {
      id: 'safety',
      title: 'Безопасность',
      icon: '🛡️',
      lessons: [
        {
          id: 'lesson_safety_1',
          num: '3.1',
          stationName: 'ст. Садва',
          title: 'Вейп в салоне вагона',
          desc: 'Курение испарителя «в кулак» и прямая угроза ложного срабатывания датчиков дыма.',
          status: 'unlocked',
          reward: '+35 Безопасность',
          duration: '2 мин',
          km: '280 км',
          incidentId: 'inc_vape_smoke_01',
        },
        {
          id: 'lesson_safety_2',
          num: '3.2',
          stationName: 'ст. Бологое',
          title: 'Бесхозный рюкзак',
          desc: 'Обнаружение забытой подозрительной сумки с проводами под креслом в проходе.',
          status: 'locked',
          reward: '+40 Безопасность',
          duration: '2.5 мин',
          km: '330 км',
          incidentId: 'inc_unclaimed_bag_01',
        },
        {
          id: 'lesson_safety_3',
          num: '3.3',
          stationName: 'ст. Валдай',
          title: 'Аварийные протоколы',
          desc: 'Действия поездной бригады при падении давления в магистрали и аварийном торможении.',
          status: 'locked',
          reward: '+50 Безопасность',
          duration: '3 мин',
          km: '398 км',
          incidentId: 'inc_unclaimed_bag_01',
        },
      ],
    },
    {
      id: 'conflicts',
      title: 'Конфликтология',
      icon: '🗣️',
      lessons: [
        {
          id: 'lesson_conflicts_1',
          num: '4.1',
          stationName: 'ст. Великий Новгород',
          title: 'Звонок на весь салон',
          desc: 'Бизнес-пассажир ведет громкие переговоры по громкой связи и хамит соседям.',
          status: 'completed',
          score: 88,
          reward: '+20 Этика',
          duration: '2 мин',
          km: '530 км',
          incidentId: 'inc_noise_business_01',
        },
        {
          id: 'lesson_conflicts_2',
          num: '4.2',
          stationName: 'ст. Жаровская',
          title: 'Нетрезвый дебошир',
          desc: 'Пассажир требует коньяк и угрожает увольнением. Правила радиопереговоров с ЛНП.',
          status: 'unlocked',
          reward: '+30 Регламент',
          duration: '2.5 мин',
          km: '630 км',
          incidentId: 'inc_drunk_conflict_01',
        },
        {
          id: 'lesson_conflicts_3',
          num: '4.3',
          stationName: 'ст. Обухово',
          title: 'Съемка на телефон',
          desc: 'Блогер навязчиво снимает лица попутчиков со штатива без их согласия (152-ФЗ).',
          status: 'locked',
          reward: '+30 Этика',
          duration: '2 мин',
          km: '668 км',
          incidentId: 'inc_noise_business_01',
        },
      ],
    },
    {
      id: 'medicine',
      title: 'Доврачебная помощь',
      icon: '🩺',
      lessons: [
        {
          id: 'lesson_medicine_1',
          num: '5.1',
          stationName: 'ст. Логовежь',
          title: 'Кинетоз на 380 км/ч',
          desc: 'Укачивание и тошнота на скоростной дуге при движении против хода поезда.',
          status: 'unlocked',
          reward: '+25 Медицина',
          duration: '2 мин',
          km: '225 км',
          incidentId: 'inc_kinetosis_01',
        },
        {
          id: 'lesson_medicine_2',
          num: '5.2',
          stationName: 'ст. Тигода',
          title: 'Таблетка из сумочки',
          desc: 'Просьба дать личный анальгин или нурофен. Категорический запрет по СТО РЖД.',
          status: 'locked',
          reward: '+35 Медицина',
          duration: '2 мин',
          km: '590 км',
          incidentId: 'inc_med_pills_01',
        },
        {
          id: 'lesson_medicine_3',
          num: '5.3',
          stationName: 'ст. СПб Главный',
          title: 'Паническая атака',
          desc: 'Острая гипервентиляция и страх скорости. Техника дыхания по квадрату и эмпатия.',
          status: 'locked',
          reward: '+40 Медицина',
          duration: '3 мин',
          km: '679 км',
          incidentId: 'inc_kinetosis_01',
        },
      ],
    },
  ];

  // Активный выбранный трек
  const activeTrack = $derived(modules.find((m) => m.id === selectedTrackId) || modules[0]);

  // Подсчет общего прогресса
  const totalCompleted = $derived(
    modules.reduce((acc, m) => acc + m.lessons.filter((l) => l.status === 'completed').length, 0)
  );
  const totalLessons = 15;

  const rank = $derived(
    totalCompleted < 4
      ? '🎓 Стажер'
      : totalCompleted < 9
        ? '🥉 Младший проводник'
        : totalCompleted < 13
          ? '🥈 Проводник бизнес-класса'
          : '🥇 Старший проводник'
  );

  const examUnlocked = true; // Открыт для интерактивного голосового тестирования на защите
  const progressPercent = $derived(Math.round((totalCompleted / totalLessons) * 100));

  function selectTrack(trackId: string) {
    playClickSound();
    selectedTrackId = trackId;
  }

  async function startLesson(lesson: Lesson) {
    if (lesson.status === 'locked') {
      playErrorSound();
      return;
    }
    playSuccessSound();
    // Запускаем персональный урок через API бэкенда
    await trainWorld.startNewTrip(lesson.id);
    authStore.setRoute('simulator');
  }

  async function startVoiceExam() {
    playSuccessSound();
    // ИСПРАВЛЕНО: Теперь мы передаем 'pro', чтобы включить нужный UI с микрофоном!
    await trainWorld.startNewTrip('pro');
    authStore.setRoute('simulator');
  }
</script>

<div class="w-full max-w-5xl mx-auto p-4 sm:p-6 pb-40 md:pb-8 flex flex-col gap-6 selection:bg-amber-500 selection:text-black">
  <!-- ==================== ШАПКА АКАДЕМИИ ==================== -->
  <header class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#2d2924] pb-4">
    <div>
      <h1 class="text-lg sm:text-xl font-bold text-[#f5f3ef] tracking-wide flex items-center gap-2">
        <span>Академия проводников ВСМ</span>
        <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
          СКОРОСТЬ ДО 400 КМ/Ч
        </span>
      </h1>
      <p class="text-xs text-[#a39e95] mt-0.5">
        Пройдите тематические станции-уроки на скоростной магистрали «Белый кречет»
      </p>
    </div>

    <!-- Индикатор прогресса и текущего ранга (со скриншота) -->
    <div class="flex flex-col items-end gap-1.5 shrink-0">
      <div class="text-sm font-bold text-amber-400 flex items-center gap-1.5">
        <span>{rank}</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-32 h-2 bg-[#282420] rounded-full overflow-hidden border border-[#3d3831]">
          <div
            class="h-full bg-gradient-to-r from-amber-600 to-yellow-400 rounded-full transition-all duration-500"
            style="width: {progressPercent}%;"
          ></div>
        </div>
        <span class="text-[11px] text-[#a39e95] font-mono font-bold">
          {totalCompleted}/{totalLessons}
        </span>
      </div>
    </div>
  </header>

  <!-- ==================== ВЕРХНИЙ РЯД: ТАБЫ МОДУЛЕЙ ==================== -->
  <div class="flex flex-col gap-2">
    <div class="text-[11px] font-bold text-[#a39e95] uppercase tracking-wider">
      Выберите направление подготовки:
    </div>

    <!-- Горизонтальная линейка 5 модулей -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
      {#each modules as mod}
        {@const completedCount = mod.lessons.filter((l) => l.status === 'completed').length}
        {@const isSelected = selectedTrackId === mod.id}
        <button
          onclick={() => selectTrack(mod.id)}
          class="p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between gap-2 relative overflow-hidden group {isSelected
            ? 'bg-amber-950/40 border-amber-500/80 shadow-[0_0_15px_rgba(245,158,11,0.2)]'
            : 'bg-[#141210]/80 border-[#2d2924] hover:border-[#3d3831] hover:bg-[#1a1816]'}"
        >
          <!-- Активная полоса снизу -->
          {#if isSelected}
            <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 to-yellow-400"></div>
          {/if}

          <div class="flex items-center justify-between">
            <span class="text-xl group-hover:scale-110 transition-transform">{mod.icon}</span>
            <span
              class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded {completedCount === 3
                ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-600/40'
                : 'bg-[#282420] text-amber-300 border border-[#3d3831]'}"
            >
              {completedCount}/3
            </span>
          </div>

          <div>
            <div class="text-xs font-bold truncate {isSelected ? 'text-amber-300' : 'text-[#f5f3ef]'}">
              {mod.title}
            </div>
            <div class="w-full h-1 bg-[#282420] rounded-full overflow-hidden mt-1.5">
              <div
                class="h-full bg-amber-500 rounded-full"
                style="width: {(completedCount / 3) * 100}%;"
              ></div>
            </div>
          </div>
        </button>
      {/each}
    </div>
  </div>

  <!-- ==================== СЕКЦИЯ: ЖЕЛЕЗНОДОРОЖНЫЙ ПУТЬ И КАРТОЧКИ-ВАГОНЫ ==================== -->
  <div class="flex flex-col gap-3 mt-2">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="text-sm">🚄</span>
        <h2 class="text-xs sm:text-sm font-bold text-[#f5f3ef] uppercase tracking-wider">
          Линия перегонов: {activeTrack.title}
        </h2>
      </div>
      <span class="text-[11px] text-[#706b63] font-mono hidden sm:inline">
        Скроллируйте станции слева направо ➔
      </span>
    </div>

    <!-- Контейнер рельсового полотна со шпалами -->
    <div class="railway-track-wrapper p-4 sm:p-6 rounded-2xl bg-[#141210]/90 border border-[#2d2924] relative overflow-hidden">
      <!-- Металлическая колея со шпалами на фоне -->
      <div class="rail-ties-bg"></div>
      <div class="rail-line-top"></div>
      <div class="rail-line-bottom"></div>

      <!-- Горизонтальная карусель карточек (рулетка уроков) -->
      <div class="flex gap-4 sm:gap-6 overflow-x-auto pb-2 pt-1 snap-x snap-mandatory relative z-10 hide-scrollbar">
        {#each activeTrack.lessons as lesson}
          <!-- Карточка-вагон (Станция маршрута) -->
          <div
            class="snap-center min-w-[280px] sm:min-w-[310px] max-w-[320px] rounded-2xl border p-4 sm:p-5 flex flex-col justify-between gap-4 transition-all duration-200 relative group {lesson.status ===
            'completed'
              ? 'bg-[#1a1816] border-emerald-600/40 shadow-md shadow-emerald-950/20'
              : lesson.status === 'unlocked'
                ? 'bg-gradient-to-b from-[#1f1b16] to-[#141210] border-amber-500/80 shadow-[0_0_25px_rgba(245,158,11,0.25)]'
                : 'bg-[#12110f]/80 border-[#262320] opacity-60'}"
          >
            <!-- Станционный штамп / Чекпоинт -->
            <div>
              <div class="flex items-center justify-between gap-2 mb-3">
                <span
                  class="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full flex items-center gap-1 {lesson.status ===
                  'completed'
                    ? 'bg-emerald-950/70 text-emerald-300 border border-emerald-500/40'
                    : lesson.status === 'unlocked'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse'
                      : 'bg-[#282420] text-[#706b63] border border-[#3d3831]'}"
                >
                  {#if lesson.status === 'completed'}
                    <span>✓</span> <span>ПРОЙДЕНО</span>
                  {:else if lesson.status === 'unlocked'}
                    <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> <span>ДОСТУПНО</span>
                  {:else}
                    <span>🔒</span> <span>ЗАКРЫТО</span>
                  {/if}
                </span>

                <span class="text-[10px] text-[#a39e95] font-mono">
                  {lesson.km} • {lesson.duration}
                </span>
              </div>

              <!-- Название и станция -->
              <div class="text-[10px] text-amber-400/90 font-mono uppercase font-bold tracking-wider mb-0.5">
                {lesson.stationName} • Урок {lesson.num}
              </div>
              <h3 class="text-sm sm:text-base font-bold text-[#f5f3ef] mb-2 leading-snug">
                {lesson.title}
              </h3>
              <p class="text-xs text-[#a39e95] leading-relaxed line-clamp-2">
                {lesson.desc}
              </p>
            </div>

            <!-- Нижняя плашка: Награда и Кнопка старта -->
            <div class="pt-3 border-t border-[#2d2924] flex flex-col gap-2.5">
              <div class="flex items-center justify-between text-[11px] font-mono">
                <span class="text-[#706b63]">Награда ЗУН:</span>
                <span class="font-bold text-amber-300">{lesson.reward}</span>
              </div>

              {#if lesson.status === 'completed'}
                <button
                  onclick={() => startLesson(lesson)}
                  class="w-full py-2.5 px-4 rounded-xl bg-[#282420] hover:bg-[#342f2a] border border-[#3d3831] hover:border-amber-400/60 text-xs font-bold text-[#f5f3ef] transition-all cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <span>Повторить (С подсказками)</span>
                  <span class="text-amber-400">↺</span>
                </button>
              {:else if lesson.status === 'unlocked'}
                <button
                  onclick={() => startLesson(lesson)}
                  class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-amber-600 via-amber-500 to-yellow-500 hover:from-amber-500 hover:to-yellow-400 text-stone-950 text-xs font-bold tracking-wide shadow-md shadow-amber-500/25 transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer flex items-center justify-center gap-2"
                >
                  <span>🎙️ Голосовой рейс (С подсказками)</span>
                </button>
              {:else}
                <button
                  disabled
                  class="w-full py-2.5 px-4 rounded-xl bg-[#1c1a17] border border-[#2d2924] text-xs font-semibold text-[#5c5750] cursor-not-allowed flex items-center justify-center gap-1.5"
                >
                  <span>Недоступно</span>
                  <span>🔒</span>
                </button>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  </div>

  <!-- ==================== СВОБОДНЫЙ ГОЛОСОВОЙ ТРЕНАЖЕР (PRO РЕЖИМ) ==================== -->
  <div class="mt-2 pt-4 border-t border-[#2d2924]">
    <div class="text-[11px] font-bold text-amber-500 uppercase tracking-wider mb-3 flex items-center gap-2">
      <span class="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
      Свободный режим (Динамическая генерация инцидентов)
    </div>

    <div class="p-5 sm:p-6 rounded-2xl border flex flex-col md:flex-row items-center justify-between gap-5 relative overflow-hidden bg-gradient-to-r from-[#2a1708] to-[#140b04] border-amber-500/50 shadow-[0_0_20px_rgba(245,158,11,0.15)]">

      <div class="flex-1 space-y-2 relative z-10">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-2xl">🎙️</span>
          <h2 class="text-sm sm:text-base font-bold text-amber-400 uppercase tracking-wider">
            PRO-Рейс: Голосовой тренажер
          </h2>
          <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
            С ИИ-подсказками
          </span>
        </div>
        <p class="text-xs text-[#a39e95] leading-relaxed max-w-2xl">
          Сценарий будет сгенерирован ИИ-директором на основе ваших слабых зон ЗУН. Инциденты решаются голосом, <strong class="text-emerald-400">система будет давать вам подсказки</strong> по регламенту. Пассажиры (ИИ) будут отвечать вам в реальном времени. Будьте вежливы!
        </p>
      </div>

      <button
        onclick={startVoiceExam}
        class="relative z-10 shrink-0 px-6 py-3.5 rounded-xl font-bold text-xs sm:text-sm transition-all flex items-center gap-2 bg-gradient-to-r from-rose-600 via-orange-600 to-amber-500 hover:scale-105 text-white shadow-lg shadow-rose-500/30 cursor-pointer border border-rose-400/50"
      >
        <span>🔥 Запустить PRO-рейс ➔</span>
      </button>
    </div>
  </div>
</div>

<style>
  /* Железнодорожное полотно ВСМ: рельсы и шпалы */
  .railway-track-wrapper {
    position: relative;
  }

  /* Шпалы (повторяющиеся штрихи) */
  .rail-ties-bg {
    position: absolute;
    left: 0;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    height: 48px;
    background-image: repeating-linear-gradient(
      90deg,
      rgba(61, 56, 49, 0.45) 0px,
      rgba(61, 56, 49, 0.45) 5px,
      transparent 5px,
      transparent 28px
    );
    pointer-events: none;
    z-index: 1;
  }

  /* Верхний рельс */
  .rail-line-top {
    position: absolute;
    left: 0;
    right: 0;
    top: calc(50% - 16px);
    height: 2px;
    background: linear-gradient(90deg, #3d3831, rgba(245, 158, 11, 0.6), #3d3831);
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.3);
    pointer-events: none;
    z-index: 2;
  }

  /* Нижний рельс */
  .rail-line-bottom {
    position: absolute;
    left: 0;
    right: 0;
    top: calc(50% + 16px);
    height: 2px;
    background: linear-gradient(90deg, #3d3831, rgba(245, 158, 11, 0.6), #3d3831);
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.3);
    pointer-events: none;
    z-index: 2;
  }

  /* Скрытие полосы прокрутки для рулетки */
  .hide-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
  .hide-scrollbar::-webkit-scrollbar {
    display: none;
  }
</style>