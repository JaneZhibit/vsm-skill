<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../lib/stores/authStore.svelte';
  import { playClickSound, stopAmbient } from '../lib/utils/audio';

  let selectedRole = $state<'senior' | 'trainee'>('senior');
  let isLoading = $state<boolean>(false);

  onMount(() => {
    stopAmbient();
  });

  async function handleLogin() {
    playClickSound();
    isLoading = true;
    try {
      await authStore.loginAsGuest(selectedRole);
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="h-screen w-screen overflow-hidden bg-[#0f0e0d] flex items-center justify-center p-4 select-none selection:bg-amber-500 selection:text-black">
  <!-- Карточка авторизации: строго 400px шириной, теплый графит и матовое золото -->
  <div class="login-card w-[400px] max-w-[92vw] rounded-2xl bg-[#1a1816]/90 border border-[#2d2924] p-7 shadow-2xl flex flex-col items-center text-center">
    <!-- Логотип ВСМ в золотистых тонах 1-го класса -->
    <div class="w-13 h-13 rounded-xl bg-gradient-to-tr from-amber-600 via-amber-500 to-yellow-500 flex items-center justify-center font-extrabold text-lg text-stone-950 shadow-lg shadow-amber-500/20 border border-amber-400/30 mb-4">
      ВСМ
    </div>

    <!-- Заголовок -->
    <h1 class="text-lg font-bold text-[#f5f3ef] tracking-wide">
      Штаб проводников ВСМ-1
    </h1>
    <p class="text-xs text-[#a39e95] mt-1 mb-5">
      Тренажер профессиональных компетенций ЗУН
    </p>

    <!-- Выбор роли: компактные кнопки -->
    <div class="w-full mb-5">
      <div class="text-[11px] font-semibold text-[#a39e95] uppercase tracking-wider mb-2 text-left">
        Роль сотрудника:
      </div>

      <div class="grid grid-cols-2 gap-2">
        <button
          type="button"
          onclick={() => { selectedRole = 'senior'; playClickSound(); }}
          class="p-2.5 rounded-xl border text-left transition-all cursor-pointer {selectedRole === 'senior'
            ? 'bg-amber-950/40 border-amber-500/80 text-amber-300'
            : 'bg-[#141210]/60 border-[#2d2924] text-[#a39e95] hover:border-[#3d3831]'}"
        >
          <div class="text-xs font-bold text-[#f5f3ef]">Старший проводник</div>
          <div class="text-[10px] text-[#a39e95] mt-0.5">Бизнес-класс • 14 смен</div>
        </button>

        <button
          type="button"
          onclick={() => { selectedRole = 'trainee'; playClickSound(); }}
          class="p-2.5 rounded-xl border text-left transition-all cursor-pointer {selectedRole === 'trainee'
            ? 'bg-amber-950/40 border-amber-500/80 text-amber-300'
            : 'bg-[#141210]/60 border-[#2d2924] text-[#a39e95] hover:border-[#3d3831]'}"
        >
          <div class="text-xs font-bold text-[#f5f3ef]">Стажер</div>
          <div class="text-[10px] text-[#a39e95] mt-0.5">Обучение • 2 смены</div>
        </button>
      </div>
    </div>

    <!-- Кнопка быстрого входа в золотистом градиенте -->
    <button
      onclick={handleLogin}
      disabled={isLoading}
      class="w-full py-3 px-5 rounded-xl bg-gradient-to-r from-amber-600 via-amber-500 to-yellow-500 hover:from-amber-500 hover:to-yellow-400 active:scale-[0.99] text-stone-950 font-bold text-xs sm:text-sm tracking-wide shadow-lg shadow-amber-500/20 border border-amber-400/40 transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
    >
      {#if isLoading}
        <span>Подключение к SQLite...</span>
      {:else}
        <span>🚄 Быстрый вход в систему</span>
      {/if}
    </button>

    <!-- Подпись безопасности -->
    <div class="mt-4 pt-3 border-t border-[#2d2924] w-full text-[10px] text-[#706b63] font-mono">
      База данных SQLite • ЕКАСУТР ВСМ
    </div>
  </div>
</div>

<style>
  .login-card {
    backdrop-filter: blur(16px);
  }
</style>
