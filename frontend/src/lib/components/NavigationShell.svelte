<script lang="ts">
  import type { Snippet } from 'svelte';
  import { authStore, type AppRoute } from '../stores/authStore.svelte';
  import { trainWorld } from '../stores/trainWorld.svelte';
  import { playClickSound } from '../utils/audio';

  interface Props {
    children: Snippet;
  }

  let { children }: Props = $props();

  const navItems = [
    { route: 'trips' as AppRoute, label: 'Учебные рейсы', icon: '🚄' },
    { route: 'dashboard' as AppRoute, label: 'Мой профиль', icon: '👤' },
    { route: 'leaderboard' as AppRoute, label: 'Рейтинг', icon: '🏆' },
    { route: 'studio' as AppRoute, label: 'База знаний', icon: '📚' },
  ];

  function handleNav(target: AppRoute) {
    playClickSound();
    authStore.setRoute(target);
  }

  function handleLogout() {
    playClickSound();
    authStore.logout();
  }

  const conductorName = $derived(authStore.currentUser?.name || trainWorld.conductorProfile.name);
  const conductorRole = $derived(authStore.currentUser?.role || trainWorld.conductorProfile.role);
</script>

<div class="h-screen w-screen overflow-hidden bg-[#0f0e0d] text-[#f5f3ef] flex flex-col md:flex-row select-none">
  <!-- DESKTOP SIDEBAR -->
  <aside class="hidden md:flex flex-col justify-between w-60 h-full bg-[#141210] border-r border-[#262320] p-4 shrink-0 z-40">
    <div class="flex flex-col gap-6">
      <!-- Логотип -->
      <div class="flex items-center gap-3 px-1 pt-1">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-600 to-yellow-500 flex items-center justify-center font-bold text-sm text-stone-950 shadow-md">
          ВСМ
        </div>
        <div>
          <div class="font-bold text-sm text-white">Тренажер бригад</div>
          <div class="text-[10px] text-[#706b63] font-mono">Скоростной поезд</div>
        </div>
      </div>

      <!-- Профиль в сайдбаре -->
      <div class="p-3 rounded-xl bg-[#1a1816] border border-[#282420] flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-[#24201c] flex items-center justify-center text-sm">
          {conductorRole.includes('Старший') ? '👨‍✈️' : '👨‍💼'}
        </div>
        <div class="overflow-hidden">
          <div class="text-xs font-bold text-white truncate">{conductorName}</div>
          <div class="text-[10px] text-amber-400/90 truncate">{conductorRole}</div>
        </div>
      </div>

      <!-- Навигация -->
      <nav class="flex flex-col gap-1">
        {#each navItems as item}
          {@const isActive = authStore.currentRoute === item.route}
          <button
            onclick={() => handleNav(item.route)}
            class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all cursor-pointer text-left {isActive
              ? 'bg-[#201d19] text-amber-300 border border-[#3d3831]'
              : 'text-[#a39e95] hover:text-white hover:bg-[#1a1816] border border-transparent'}"
          >
            <span class="text-base">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        {/each}
      </nav>
    </div>

    <!-- Нижняя часть -->
    <div class="pt-3 border-t border-[#262320] flex items-center justify-between px-1">
      <span class="text-[10px] text-[#5c5750]">Учебный центр</span>
      <button
        onclick={handleLogout}
        class="text-xs text-[#a39e95] hover:text-rose-400 transition-colors cursor-pointer"
      >
        Выйти
      </button>
    </div>
  </aside>

  <!-- КОНТЕНТНАЯ ОБЛАСТЬ -->
  <main class="flex-1 h-full w-full overflow-y-auto pb-16 md:pb-0 relative flex flex-col">
    {@render children()}
  </main>

  <!-- MOBILE BOTTOM NAV -->
  <nav class="md:hidden fixed bottom-0 left-0 right-0 h-14 bg-[#141210] border-t border-[#262320] grid grid-cols-4 items-center z-50">
    {#each navItems as item}
      {@const isActive = authStore.currentRoute === item.route}
      <button
        onclick={() => handleNav(item.route)}
        class="flex flex-col items-center justify-center gap-0.5 h-full cursor-pointer {isActive
          ? 'text-amber-400 font-semibold'
          : 'text-[#706b63]'}"
      >
        <span class="text-base leading-none">{item.icon}</span>
        <span class="text-[10px]">{item.label}</span>
      </button>
    {/each}
  </nav>
</div>
