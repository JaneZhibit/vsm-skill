<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../lib/stores/authStore.svelte';
  import { trainWorld } from '../lib/stores/trainWorld.svelte';
  import RadarChart from '../lib/components/RadarChart.svelte';
  import LmsReportModal from '../lib/components/LmsReportModal.svelte';
  import { playClickSound, stopAmbient } from '../lib/utils/audio';

  let activeTab = $state<'skills' | 'rating'>('skills');
  let isReportOpen = $state<boolean>(false);
  let reportData = $state<any>(null);
  let isReportLoading = $state<boolean>(false);
  let userAchievements = $state<any[]>([]);

  // Каталог достижений по реальным сценариям
  const achievementsList = [
    {
      code: 'first_trip',
      title: 'Первый рейс',
      description: 'Успешное завершение смены по графику',
      icon: '🚄',
    },
    {
      code: 'safety_first',
      title: 'Безопасность',
      description: 'Предотвращение пожарной тревоги из-за вейпа',
      icon: '🛡️',
    },
    {
      code: 'med_hero',
      title: 'Первая помощь',
      description: 'Грамотные действия при кинетозе пассажира',
      icon: '🩺',
    },
    {
      code: 'sto_expert',
      title: 'Знаток правил',
      description: 'Отказ в выдаче личных таблеток по регламенту',
      icon: '📜',
    },
  ];

  const conductorName = $derived(authStore.currentUser?.name || trainWorld.conductorProfile.name);
  const conductorRole = $derived(authStore.currentUser?.role || trainWorld.conductorProfile.role);
  const shiftsCount = $derived(authStore.currentUser?.shifts || trainWorld.conductorProfile.shiftsCompleted);
  const currentId = $derived(authStore.currentUser?.id || 'u-senior-01');

  async function loadAchievements() {
    try {
      const res = await fetch(`/api/v1/users/${encodeURIComponent(currentId)}/achievements`);
      if (res.ok) userAchievements = await res.json();
    } catch {}
  }

  async function handleOpenReport() {
    playClickSound();
    isReportLoading = true;
    try {
      const res = await fetch(`/api/v1/users/${encodeURIComponent(currentId)}/lms-report`);
      if (res.ok) {
        reportData = await res.json();
        isReportOpen = true;
      }
    } catch (err) {
      console.error('Ошибка загрузки аттестации:', err);
    } finally {
      isReportLoading = false;
    }
  }

  onMount(() => {
    stopAmbient();
    authStore.fetchLeaderboard();
    authStore.fetchMe();
    loadAchievements();
  });

  async function handleStartTrip() {
    playClickSound();
    await trainWorld.startNewTrip('level_1');
    authStore.setRoute('simulator');
  }

  function handleLogout() {
    playClickSound();
    authStore.logout();
  }

  const ratingList = $derived.by(() => {
    if (authStore.leaderboardData && authStore.leaderboardData.length > 0) {
      return authStore.leaderboardData.map((m, idx) => ({
        rank: idx + 1,
        medal: idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : `${idx + 1}`,
        id: m.id,
        name: m.username,
        role: m.role,
        score: m.loyalty_score,
        isCurrent: m.id === currentId || m.username === conductorName,
      }));
    }
    return [];
  });
</script>

<div class="h-full w-full overflow-y-auto bg-[#0f0e0d] text-[#f5f3ef] flex flex-col">
  <div class="max-w-4xl w-full mx-auto p-4 sm:p-6 flex flex-col gap-6 flex-1">

    <!-- ==================== ШАПКА ПРОФИЛЯ ==================== -->
    <header class="bg-[#1a1816] border border-[#2d2924] rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div class="flex items-center gap-3.5">
        <div class="w-12 h-12 rounded-xl bg-[#282420] border border-[#3d3831] flex items-center justify-center text-2xl">
          {conductorRole.includes('Старший') ? '👨✈️' : '👨💼'}
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-base font-bold text-white">{conductorName}</h1>
            <span class="text-xs text-[#a39e95]">• {shiftsCount} смен</span>
          </div>
          <div class="flex items-center gap-3 mt-0.5">
            <span class="text-xs text-amber-400/90 font-medium">{conductorRole}</span>
            <button
              onclick={handleLogout}
              class="text-[11px] text-[#706b63] hover:text-rose-400 transition-colors cursor-pointer"
            >
              Сменить профиль
            </button>
          </div>
        </div>
      </div>

      <!-- Главная кнопка действия -->
      <div class="flex items-center gap-2.5 w-full sm:w-auto">
        <button
          onclick={handleOpenReport}
          class="px-3.5 py-2.5 rounded-xl bg-[#201d19] hover:bg-[#282420] border border-[#3d3831] text-xs font-semibold text-[#d6d3d1] hover:text-white transition-all cursor-pointer"
          title="Просмотр официального допуска к рейсам"
        >
          {isReportLoading ? 'Загрузка...' : 'Допуск к рейсам'}
        </button>

        <button
          onclick={handleStartTrip}
          class="flex-1 sm:flex-none px-6 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-stone-950 font-bold text-xs sm:text-sm tracking-wide shadow-md transition-all cursor-pointer flex items-center justify-center gap-2"
        >
          <span>Начать рейс</span>
          <span>➔</span>
        </button>
      </div>
    </header>

    <!-- ==================== ИГРОВОЙ ВЫЗОВ (ЧЕЛЛЕНДЖ) ==================== -->
    <div class="p-4 rounded-xl bg-[#141210] border border-amber-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-base">
          🎯
        </div>
        <div>
          <div class="text-xs font-bold text-amber-300">
            Тренировка недели: Оказание первой помощи
          </div>
          <p class="text-xs text-[#a39e95] mt-0.5">
            Подтвердите навык помощи при кинетозе, чтобы сохранить рейтинг допуска.
          </p>
        </div>
      </div>

      <button
        onclick={handleStartTrip}
        class="px-3.5 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/50 text-amber-300 text-xs font-semibold cursor-pointer transition-all shrink-0"
      >
        Пройти кейс ➔
      </button>
    </div>

    <!-- ==================== ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК ==================== -->
    <div class="flex items-center justify-between border-b border-[#2d2924] pb-2">
      <div class="flex gap-2">
        <button
          onclick={() => { activeTab = 'skills'; playClickSound(); }}
          class="px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-all {activeTab === 'skills'
            ? 'bg-[#201d19] text-amber-300 border border-[#3d3831]'
            : 'text-[#a39e95] hover:text-white'}"
        >
          Мои навыки
        </button>

        <button
          onclick={() => { activeTab = 'rating'; playClickSound(); }}
          class="px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-all {activeTab === 'rating'
            ? 'bg-[#201d19] text-amber-300 border border-[#3d3831]'
            : 'text-[#a39e95] hover:text-white'}"
        >
          Рейтинг проводников
        </button>
      </div>

      <span class="text-xs text-[#706b63] font-mono">
        Квалификация: <strong class="text-amber-400 font-bold">{trainWorld.overallReadiness}%</strong>
      </span>
    </div>

    <!-- ==================== ВКЛАДКА 1: НАВЫКИ ==================== -->
    {#if activeTab === 'skills'}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-5 items-stretch">
        <!-- Радар и список навыков -->
        <section class="bg-[#161412] border border-[#2d2924] rounded-2xl p-4 sm:p-5 flex flex-col justify-between">
          <div class="flex items-center justify-center py-1">
            <RadarChart />
          </div>

          <div class="grid grid-cols-2 gap-2 pt-3 border-t border-[#2d2924] text-xs">
            <div class="p-2 rounded-lg bg-[#141210] border border-[#282420] flex justify-between">
              <span class="text-[#a39e95]">Безопасность</span>
              <strong class="font-mono text-amber-400">{trainWorld.skills.safety_tech}%</strong>
            </div>
            <div class="p-2 rounded-lg bg-[#141210] border border-[#282420] flex justify-between">
              <span class="text-[#a39e95]">Сервис</span>
              <strong class="font-mono text-amber-400">{trainWorld.skills.service_psychology}%</strong>
            </div>
            <div class="p-2 rounded-lg bg-[#141210] border border-[#282420] flex justify-between">
              <span class="text-[#a39e95]">Регламент</span>
              <strong class="font-mono text-amber-400">{trainWorld.skills.routine_discipline}%</strong>
            </div>
            <div class="p-2 rounded-lg bg-[#141210] border border-[#282420] flex justify-between">
              <span class="text-[#a39e95]">Первая помощь</span>
              <strong class="font-mono text-amber-400">{trainWorld.skills.first_aid}%</strong>
            </div>
          </div>
        </section>

        <!-- Персональный фокус обучения -->
        <section class="bg-[#161412] border border-[#2d2924] rounded-2xl p-4 sm:p-5 flex flex-col justify-between gap-4">
          <div class="space-y-3">
            <div class="text-xs font-bold uppercase tracking-wider text-[#a39e95]">
              Рекомендация инструктора
            </div>

            <div class="p-3.5 rounded-xl bg-amber-950/20 border border-amber-800/30 space-y-1">
              <div class="text-xs font-bold text-amber-300">
                Слабая зона: {trainWorld.weakestSkill.name} ({trainWorld.weakestSkill.score}%)
              </div>
              <p class="text-xs text-[#a39e95] leading-relaxed">
                {trainWorld.weakestSkill.recommendation}
              </p>
            </div>

            <div class="p-3 rounded-xl bg-[#141210] border border-[#282420] space-y-1.5 text-xs">
              <div class="flex justify-between">
                <span class="text-[#706b63]">Маршрут:</span>
                <span class="text-[#d6d3d1]">Москва — Санкт-Петербург</span>
              </div>
              <div class="flex justify-between">
                <span class="text-[#706b63]">Поезд:</span>
                <span class="text-[#d6d3d1]">«Белый кречет» (400 км/ч)</span>
              </div>
              <div class="flex justify-between">
                <span class="text-[#706b63]">Вагон:</span>
                <span class="text-amber-400 font-semibold">Вагон 1-го класса</span>
              </div>
            </div>
          </div>

          <button
            onclick={handleStartTrip}
            class="w-full py-2.5 rounded-xl bg-[#24201c] hover:bg-[#2d2823] border border-[#3d3831] text-xs font-bold text-amber-300 transition-all cursor-pointer flex items-center justify-center gap-1.5"
          >
            <span>Отработать слабый навык в рейсе</span>
            <span>➔</span>
          </button>
        </section>
      </div>

      <!-- Достижения -->
      <section class="bg-[#161412] border border-[#2d2924] rounded-2xl p-4 sm:p-5 flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <h2 class="text-xs font-bold uppercase tracking-wider text-[#a39e95]">
            Квалификационные знаки
          </h2>
          <span class="text-xs font-mono text-amber-400">
            {userAchievements.length} из {achievementsList.length}
          </span>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {#each achievementsList as ach}
            {@const isUnlocked = userAchievements.some(u => u.code === ach.code) || (ach.code === 'first_trip' && shiftsCount > 0)}
            <div class="p-3 rounded-xl border flex flex-col justify-between gap-2 transition-all {isUnlocked
              ? 'bg-[#1c1915] border-amber-500/40 text-white'
              : 'bg-[#141210]/50 border-[#282420] opacity-50'}">
              <div class="flex items-center justify-between">
                <span class="text-xl">{ach.icon}</span>
                <span class="text-[9px] font-mono font-semibold px-1.5 py-0.5 rounded {isUnlocked ? 'bg-emerald-950 text-emerald-300' : 'bg-[#201d19] text-[#706b63]'}">
                  {isUnlocked ? 'Открыто' : 'Закрыто'}
                </span>
              </div>
              <div>
                <div class="text-xs font-bold">{ach.title}</div>
                <div class="text-[11px] text-[#a39e95] mt-0.5 leading-snug">{ach.description}</div>
              </div>
            </div>
          {/each}
        </div>
      </section>

    <!-- ==================== ВКЛАДКА 2: РЕЙТИНГ ==================== -->
    {:else}
      <section class="bg-[#161412] border border-[#2d2924] rounded-2xl p-4 sm:p-5">
        <div class="space-y-2">
          {#each ratingList as member}
            <div class="flex items-center justify-between p-3 rounded-xl border transition-all {member.isCurrent
              ? 'bg-amber-950/20 border-amber-500/50 text-white'
              : 'bg-[#141210] border-[#282420] text-[#a39e95]'}">
              <div class="flex items-center gap-3">
                <span class="w-6 text-center font-bold font-mono">{member.medal}</span>
                <div>
                  <div class="text-xs font-bold {member.isCurrent ? 'text-amber-300' : 'text-white'}">
                    {member.name} {member.isCurrent ? '(Вы)' : ''}
                  </div>
                  <div class="text-[11px] text-[#706b63]">{member.role}</div>
                </div>
              </div>
              <div class="text-xs font-mono font-bold text-amber-400">
                {member.score} баллов
              </div>
            </div>
          {/each}
        </div>
      </section>
    {/if}

  </div>

  <LmsReportModal isOpen={isReportOpen} onClose={() => { isReportOpen = false; }} report={reportData} />
</div>
