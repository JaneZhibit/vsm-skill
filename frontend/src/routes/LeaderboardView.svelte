<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../lib/stores/authStore.svelte';

  onMount(() => {
    authStore.fetchLeaderboard();
  });

  const currentId = $derived(authStore.currentUser?.id || 'u-senior-01');
  const currentName = $derived(authStore.currentUser?.name || '');

  const displayLeaderboard = $derived.by(() => {
    if (authStore.leaderboardData && authStore.leaderboardData.length > 0) {
      return authStore.leaderboardData.map((m, idx) => ({
        rank: idx + 1,
        medal: idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : `${idx + 1}`,
        id: m.id,
        name: m.username,
        role: m.role,
        points: m.loyalty_score,
        badge: m.badge,
        isCurrent: m.id === currentId || m.username === currentName,
      }));
    }
    return [];
  });
</script>

<div class="w-full max-w-5xl mx-auto p-4 sm:p-6 pb-28 md:pb-8 flex flex-col gap-6">
  <header class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#2d2924] pb-4">
    <div>
      <h1 class="text-lg sm:text-xl font-bold text-[#f5f3ef] tracking-wide">Рейтинг поездных бригад ВСМ</h1>
      <p class="text-xs text-[#a39e95] mt-0.5">Единая система квалификации проводников скоростного движения</p>
    </div>
    <!-- Плашка сгорающих баллов (требование ТЗ) -->
    <div class="p-2.5 rounded-xl bg-amber-950/30 border border-amber-500/40 text-xs flex items-center gap-2 text-amber-300">
      <span>⏳</span>
      <span>Сгорающие баллы: <strong>48 часов</strong> до обновления рейтинга смены</span>
    </div>
  </header>

  {#if authStore.isLoadingLeaderboard}
    <div class="py-16 text-center text-xs text-[#a39e95] animate-pulse">Загрузка данных из SQLite...</div>
  {:else}
    <div class="space-y-2.5">
      {#each displayLeaderboard as member}
        <div class="flex items-center justify-between p-3.5 rounded-xl border transition-all {member.isCurrent ? 'bg-amber-950/40 border-amber-500/70 shadow-lg shadow-amber-500/10' : 'bg-[#141210]/60 border-[#2d2924] text-[#a39e95]'}"
        >
          <div class="flex items-center gap-3.5">
            <span class="text-base w-6 text-center font-mono font-bold {member.rank <= 3 ? '' : 'text-[#706b63]'}">
              {member.medal}
            </span>
            <div>
              <div class="text-xs font-bold {member.isCurrent ? 'text-amber-300' : 'text-[#f5f3ef]'} flex items-center gap-2">
                <span>{member.name}</span>
                {#if member.isCurrent}
                  <span class="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 font-mono font-semibold">ВЫ</span>
                {/if}
              </div>
              <div class="text-[11px] text-[#a39e95]">{member.role}</div>
            </div>
          </div>
          <div class="text-right">
            <span class="text-xs font-bold font-mono {member.isCurrent ? 'text-amber-300' : 'text-[#f5f3ef]'}">{member.points} б.</span>
            <span class="text-[10px] text-[#706b63] block font-mono">{member.badge}</span>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
