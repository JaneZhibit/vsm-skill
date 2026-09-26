<script lang="ts">
  import { onMount } from 'svelte';
  import Login from './routes/Login.svelte';
  import Dashboard from './routes/Dashboard.svelte';
  import Simulator from './routes/Simulator.svelte';
  import TripsHub from './routes/TripsHub.svelte';
  import LeaderboardView from './routes/LeaderboardView.svelte';
  import Studio from './routes/Studio.svelte';
  import NavigationShell from './lib/components/NavigationShell.svelte';
  import DebugBar from './lib/components/DebugBar.svelte';
  import AchievementToast from './lib/components/AchievementToast.svelte';
  import { authStore } from './lib/stores/authStore.svelte';
  import { trainWorld } from './lib/stores/trainWorld.svelte';

  let showDebugBar = $state<boolean>(false);

  onMount(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey && e.shiftKey && (e.key === 'D' || e.key === 'd')) || e.key === '`') {
        showDebugBar = !showDebugBar;
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  });
</script>

<main class="h-screen w-screen overflow-hidden bg-[#0f0e0d] text-[#f5f3ef] flex flex-col selection:bg-amber-500 selection:text-black select-none">
  {#if authStore.currentRoute === 'login'}
    <Login />
  {:else if authStore.currentRoute === 'simulator'}
    <!-- Полноэкранный тренажер в вагоне -->
    <header class="h-11 px-3 sm:px-5 border-b border-[#2d2924] bg-[#1a1816]/90 backdrop-blur-md flex items-center justify-between shrink-0 z-40">
      <div class="flex items-center space-x-2.5">
        <div class="h-7 w-7 rounded bg-gradient-to-tr from-amber-600 via-amber-500 to-yellow-500 flex items-center justify-center font-extrabold text-xs text-stone-950 shadow-md shadow-amber-500/20">
          ВСМ
        </div>
        <span class="text-xs sm:text-sm font-semibold tracking-wide text-[#f5f3ef]">
          Вагон 1-го класса • Рейс № 754
        </span>

        <!-- ДОБАВЛЕННЫЙ БЛОК: Очки в реальном времени -->
        <div class="hidden sm:flex items-center gap-3 ml-4 px-3 py-1 bg-black/50 rounded-lg border border-[#3d3831] text-xs font-mono shadow-inner">
          <span class="text-amber-400" title="Лояльность">🤝 {trainWorld.loyaltyScore}</span>
          <span class="text-emerald-400" title="Безопасность">🛡️ {trainWorld.safetyScore}</span>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <!-- Кнопка управления фоновым звуком поезда -->
        <button
          data-audio-toggle
          onclick={() => trainWorld.toggleAudio()}
          class="flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-medium border transition-all cursor-pointer {trainWorld.isAudioMuted
            ? 'bg-[#282420] border-[#3d3831] text-[#a39e95] hover:text-[#f5f3ef] hover:bg-[#342f2a]'
            : 'bg-amber-950/50 border-amber-500/60 text-amber-300 shadow-[0_0_12px_rgba(245,158,11,0.3)] hover:bg-amber-900/50'}"
          title={trainWorld.isAudioMuted ? 'Включить звук поезда' : 'Выключить звук поезда'}
        >
          {#if trainWorld.isAudioMuted}
            <span class="text-xs">🔇</span>
            <span>Звук выкл</span>
          {:else}
            <span class="text-xs animate-pulse">🔊</span>
            <span class="font-semibold">Звук поезда</span>
            <span class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping"></span>
          {/if}
        </button>

        <button
          onclick={() => { trainWorld.abortTrip(); authStore.setRoute('trips'); }}
          class="flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-semibold bg-[#282420] hover:bg-[#342f2a] text-amber-300 border border-[#3d3831] cursor-pointer"
        >
          <span>⬅</span> <span>В меню</span>
        </button>
      </div>
    </header>
    <section class="flex-1 w-full h-full min-h-0 relative overflow-hidden flex flex-col">
      <Simulator />
    </section>
  {:else}
    <!-- Основной интерфейс приложения с боковой и нижней навигацией -->
    <NavigationShell>
      {#if authStore.currentRoute === 'trips'}
        <TripsHub />
      {:else if authStore.currentRoute === 'dashboard'}
        <Dashboard />
      {:else if authStore.currentRoute === 'leaderboard'}
        <LeaderboardView />
      {:else if authStore.currentRoute === 'studio'}
        <Studio />
      {/if}
    </NavigationShell>
  {/if}

  {#if showDebugBar}
    <DebugBar />
  {/if}

  <!-- Глобальный тост достижений -->
  <AchievementToast />
</main>
