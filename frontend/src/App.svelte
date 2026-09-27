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

<!-- ИСПРАВЛЕНИЕ: h-[100dvh] вместо h-screen -->
<main class="h-[100dvh] w-screen overflow-hidden bg-[#0f0e0d] text-[#f5f3ef] flex flex-col selection:bg-amber-500 selection:text-black select-none">
  {#if authStore.currentRoute === 'login'}
    <Login />
  {:else if authStore.currentRoute === 'simulator'}
    <!-- Полноэкранный тренажер в вагоне без верхней панели -->
    <section class="flex-1 w-full h-full min-h-0 relative overflow-hidden flex flex-col">
      <Simulator />
    </section>
  {:else}
    <!-- Основной интерфейс приложения -->
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