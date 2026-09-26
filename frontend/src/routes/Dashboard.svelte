<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../lib/stores/authStore.svelte';
  import { trainWorld } from '../lib/stores/trainWorld.svelte';
  import { conductorState } from '../lib/stores/conductorState.svelte';
  import RadarChart from '../lib/components/RadarChart.svelte';
  import LmsReportModal from '../lib/components/LmsReportModal.svelte';
  import { playClickSound, stopAmbient } from '../lib/utils/audio';

  let activeTab = $state<'skills' | 'rating'>('skills');
  let isReportOpen = $state<boolean>(false);
  let reportData = $state<any>(null);
  let isReportLoading = $state<boolean>(false);
  let userAchievements = $state<any[]>([]);

  const achievementsList = [
    { code: 'first_trip', title: 'Первый рейс', description: 'Успешное завершение смены', icon: '🚄' },
    { code: 'safety_first', title: 'Безопасность', description: 'Предотвращение пожарной тревоги', icon: '🛡️' },
    { code: 'med_hero', title: 'Первая помощь', description: 'Грамотные действия при кинетозе', icon: '🩺' },
    { code: 'sto_expert', title: 'Знаток правил', description: 'Отказ в выдаче лекарств (СТО РЖД)', icon: '📜' },
    { code: 'team_player', title: 'Командная работа', description: 'Привлечение ЛНП или пассажиров', icon: '🤝' },
  ];

  const cProfile = $derived(conductorState.conductorProfile);
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
      if (res.ok) { reportData = await res.json(); isReportOpen = true; }
    } finally { isReportLoading = false; }
  }

  onMount(() => {
    stopAmbient();
    authStore.fetchLeaderboard();
    authStore.fetchMe();
    loadAchievements();
  });

  function handleGoToTrips() {
    playClickSound();
    authStore.setRoute('trips');
  }

  function handleLogout() {
    playClickSound(); authStore.logout();
  }

  const ratingList = $derived.by(() => {
    if (authStore.leaderboardData?.length > 0) {
      return authStore.leaderboardData.map((m, idx) => ({
        rank: idx + 1, medal: idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : `${idx + 1}`,
        id: m.id, name: m.username, role: m.role, score: m.rating_score,
        isCurrent: m.id === currentId,
      }));
    }
    return [];
  });
</script>

<div class="h-full w-full overflow-y-auto bg-[#0f0e0d] text-[#f5f3ef] flex flex-col">
  <div class="max-w-4xl w-full mx-auto p-4 sm:p-6 flex flex-col gap-6 flex-1">

    <!-- ШАПКА ПРОФИЛЯ С ОГОНЬКАМИ -->
    <header class="bg-[#1a1816] border border-[#2d2924] rounded-2xl p-4 sm:p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
      <div class="flex items-center gap-4">
        <div class="w-14 h-14 rounded-xl bg-gradient-to-tr from-[#2d2924] to-[#1a1816] border border-[#3d3831] flex items-center justify-center text-3xl shadow-inner">
          {cProfile.gender === 'f' ? '👩✈️' : '👨✈️'}
        </div>
        <div>
          <div class="flex items-center gap-2.5">
            <h1 class="text-lg font-bold text-white">{cProfile.name}</h1>
            <!-- Ежедневная активность (Streak) -->
            <div class="flex items-center gap-1 bg-orange-950/40 border border-orange-500/30 px-2 py-0.5 rounded-md" title="Дней активности подряд">
              <span class="text-orange-500 text-[11px]">🔥</span>
              <span class="text-orange-400 text-[11px] font-bold font-mono">{cProfile.streakDays} дн.</span>
            </div>
          </div>
          <div class="flex items-center gap-3 mt-1">
            <span class="text-xs text-amber-400 font-medium">{cProfile.role} • {cProfile.badge}</span>
            <button onclick={handleLogout} class="text-[11px] text-[#706b63] hover:text-rose-400 transition-colors cursor-pointer underline">
              Сменить профиль
            </button>
          </div>
        </div>
      </div>

      <!-- Кнопки действий -->
      <div class="flex items-center gap-2 w-full md:w-auto">
        <button onclick={handleOpenReport} class="px-4 py-2.5 rounded-xl bg-[#201d19] hover:bg-[#282420] border border-[#3d3831] text-xs font-semibold text-[#d6d3d1] hover:text-white transition-all cursor-pointer">
          {isReportLoading ? 'Загрузка...' : 'Допуск к рейсам'}
        </button>
        <button onclick={handleGoToTrips} class="flex-1 md:flex-none px-6 py-2.5 rounded-xl bg-gradient-to-r from-amber-600 to-yellow-500 hover:from-amber-500 text-stone-950 font-bold text-xs sm:text-sm shadow-md transition-all cursor-pointer flex justify-center gap-2">
          <span>Перейти к рейсам ➔</span>
        </button>
      </div>
    </header>

    <!-- СТАТИСТИКА УСПЕВАЕМОСТИ -->
    <div class="grid grid-cols-3 gap-3">
      <div class="p-3 rounded-xl bg-[#141210] border border-[#2d2924] flex flex-col items-center justify-center text-center">
        <span class="text-[10px] text-[#706b63] uppercase font-bold tracking-wider mb-1">Рейтинг</span>
        <span class="text-xl font-bold font-mono text-amber-400">{cProfile.ratingScore}</span>
      </div>
      <div class="p-3 rounded-xl bg-[#141210] border border-[#2d2924] flex flex-col items-center justify-center text-center">
        <span class="text-[10px] text-[#706b63] uppercase font-bold tracking-wider mb-1">Решено кейсов</span>
        <span class="text-xl font-bold font-mono text-white">{cProfile.incidentsResolved}</span>
      </div>
      <div class="p-3 rounded-xl bg-[#141210] border border-[#2d2924] flex flex-col items-center justify-center text-center">
        <span class="text-[10px] text-[#706b63] uppercase font-bold tracking-wider mb-1">Точность</span>
        <span class="text-xl font-bold font-mono {cProfile.accuracyPercent >= 80 ? 'text-emerald-400' : 'text-rose-400'}">{cProfile.accuracyPercent}%</span>
      </div>
    </div>

    <!-- ТАБЫ -->
    <div class="flex items-center justify-between border-b border-[#2d2924] pb-2 mt-2">
      <div class="flex gap-2">
        <button onclick={() => { activeTab = 'skills'; playClickSound(); }} class="px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-all {activeTab === 'skills' ? 'bg-[#201d19] text-amber-300 border border-[#3d3831]' : 'text-[#a39e95] hover:text-white'}">
          Мои навыки
        </button>
        <button onclick={() => { activeTab = 'rating'; playClickSound(); }} class="px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-all {activeTab === 'rating' ? 'bg-[#201d19] text-amber-300 border border-[#3d3831]' : 'text-[#a39e95] hover:text-white'}">
          Лидерборд (Комплексный)
        </button>
      </div>
      <span class="text-xs text-[#706b63] font-mono hidden sm:block">Квалификация ЗУН: <strong class="text-amber-400 font-bold">{trainWorld.overallReadiness}%</strong></span>
    </div>

    <!-- КОНТЕНТ ТАБОВ -->
    {#if activeTab === 'skills'}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-5 items-stretch">
        <section class="bg-[#161412] border border-[#2d2924] rounded-2xl p-4 flex flex-col justify-between">
          <div class="flex items-center justify-center py-1"><RadarChart /></div>
          <div class="grid grid-cols-2 gap-2 pt-3 border-t border-[#2d2924] text-xs">
            <div class="p-2 rounded-lg bg-[#141210] border border-[#282420] flex justify-between"><span class="text-[#a39e95]">Безопасность</span><strong class="font-mono text-amber-400">{trainWorld.skills.safety_tech}%</strong></div>
            <div class="p-2 rounded-lg bg-[#141210] border border-[#282420] flex justify-between"><span class="text-[#a39e95]">Сервис</span><strong class="font-mono text-amber-400">{trainWorld.skills.service_psychology}%</strong></div>
            <div class="p-2 rounded-lg bg-[#141210] border border-[#282420] flex justify-between"><span class="text-[#a39e95]">Регламент</span><strong class="font-mono text-amber-400">{trainWorld.skills.routine_discipline}%</strong></div>
            <div class="p-2 rounded-lg bg-[#141210] border border-[#282420] flex justify-between"><span class="text-[#a39e95]">Медицина</span><strong class="font-mono text-amber-400">{trainWorld.skills.first_aid}%</strong></div>
          </div>
        </section>
        <section class="bg-[#161412] border border-[#2d2924] rounded-2xl p-4 flex flex-col justify-between gap-4">
          <div class="space-y-3">
            <div class="text-xs font-bold uppercase tracking-wider text-[#a39e95]">ИИ-Рекомендация</div>
            <div class="p-3.5 rounded-xl bg-amber-950/20 border border-amber-800/30 space-y-1">
              <div class="text-xs font-bold text-amber-300">Фокус: {trainWorld.weakestSkill.name} ({trainWorld.weakestSkill.score}%)</div>
              <p class="text-xs text-[#a39e95] leading-relaxed">{trainWorld.weakestSkill.recommendation}</p>
            </div>
          </div>
          <button onclick={handleGoToTrips} class="w-full py-2.5 rounded-xl bg-[#24201c] hover:bg-[#2d2823] border border-[#3d3831] text-xs font-bold text-amber-300 transition-all cursor-pointer flex justify-center gap-1.5">
            <span>Перейти к обучающим рейсам ➔</span>
          </button>
        </section>
      </div>

      <!-- ДОСТИЖЕНИЯ -->
      <section class="bg-[#161412] border border-[#2d2924] rounded-2xl p-4 flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <h2 class="text-xs font-bold uppercase tracking-wider text-[#a39e95]">Квалификационные знаки</h2>
          <span class="text-xs font-mono text-amber-400">{userAchievements.length} из {achievementsList.length}</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
          {#each achievementsList as ach}
            {@const isUnlocked = userAchievements.some(u => u.code === ach.code)}
            <div class="p-3 rounded-xl border flex flex-col justify-between gap-2 transition-all {isUnlocked ? 'bg-[#1c1915] border-amber-500/40 text-white' : 'bg-[#141210]/50 border-[#282420] opacity-50'}">
              <div class="flex items-center justify-between">
                <span class="text-xl">{ach.icon}</span>
                {#if isUnlocked}<span class="text-[9px] font-mono font-semibold px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300">Открыто</span>{/if}
              </div>
              <div>
                <div class="text-[11px] font-bold leading-tight">{ach.title}</div>
                <div class="text-[9px] text-[#a39e95] mt-1 leading-snug">{ach.description}</div>
              </div>
            </div>
          {/each}
        </div>
      </section>

    {:else}
      <!-- ЛИДЕРБОРД -->
      <section class="bg-[#161412] border border-[#2d2924] rounded-2xl p-4">
        <div class="space-y-2">
          {#each ratingList as member}
            <div class="flex items-center justify-between p-3 rounded-xl border transition-all {member.isCurrent ? 'bg-amber-950/20 border-amber-500/50 text-white shadow-lg' : 'bg-[#141210] border-[#282420] text-[#a39e95]'}">
              <div class="flex items-center gap-3">
                <span class="w-6 text-center font-bold font-mono text-base">{member.medal}</span>
                <div>
                  <div class="text-xs font-bold {member.isCurrent ? 'text-amber-300' : 'text-white'}">
                    {member.name} {member.isCurrent ? '(Вы)' : ''}
                  </div>
                  <div class="text-[10px] text-[#706b63]">{member.role}</div>
                </div>
              </div>
              <div class="text-right">
                <div class="text-xs font-mono font-bold text-amber-400">{member.score} рейтинговых очков</div>
              </div>
            </div>
          {/each}
        </div>
      </section>
    {/if}
  </div>

  <LmsReportModal isOpen={isReportOpen} onClose={() => { isReportOpen = false; }} report={reportData} />
</div>
