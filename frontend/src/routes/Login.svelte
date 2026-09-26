<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore } from '../lib/stores/authStore.svelte';
  import { playClickSound, stopAmbient } from '../lib/utils/audio';

  let selectedRole = $state<'senior' | 'trainee'>('senior');
  let selectedGender = $state<'m' | 'f'>('m');
  let isLoading = $state<boolean>(false);

  onMount(() => {
    stopAmbient();
  });

  const previewProfile = $derived.by(() => {
    if (selectedRole === 'senior' && selectedGender === 'm') {
      return { name: 'Алексей Смирнов', desc: 'Старший проводник • 14 смен • Силовой и технический профиль' };
    }
    if (selectedRole === 'senior' && selectedGender === 'f') {
      return { name: 'Анна Родионова', desc: 'Старший проводник • 12 смен • Командная координация и эмпатия' };
    }
    if (selectedRole === 'trainee' && selectedGender === 'm') {
      return { name: 'Дмитрий Волков', desc: 'Проводник-стажер • 2 смены • Режим стажировки' };
    }
    return { name: 'Мария Соколова', desc: 'Проводник-стажер • 3 смены • Режим стажировки' };
  });

  async function handleLogin() {
    playClickSound();
    isLoading = true;
    try {
      await authStore.loginAsGuest(selectedRole, selectedGender);
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="h-screen w-screen overflow-hidden bg-[#0f0e0d] flex items-center justify-center p-4 select-none selection:bg-amber-500 selection:text-black">
  <div class="w-[430px] max-w-[94vw] rounded-2xl bg-[#1a1816]/95 border border-[#2d2924] p-7 shadow-2xl flex flex-col items-center text-center backdrop-blur-xl">
    <div class="w-13 h-13 rounded-xl bg-gradient-to-tr from-amber-600 via-amber-500 to-yellow-500 flex items-center justify-center font-extrabold text-lg text-stone-950 shadow-lg shadow-amber-500/20 border border-amber-400/30 mb-4">
      ВСМ
    </div>

    <h1 class="text-lg font-bold text-[#f5f3ef] tracking-wide">
      Штаб проводников ВСМ-400
    </h1>
    <p class="text-xs text-[#a39e95] mt-1 mb-5">
      Демо-вход без пароля • Выберите роль и пол проводника
    </p>

    <!-- Выбор пола проводника (влияет на реплики и механику тяжелого багажа) -->
    <div class="w-full mb-4">
      <div class="text-[11px] font-semibold text-[#a39e95] uppercase tracking-wider mb-2 text-left">
        1. Пол проводника (влияет на диалоги и действия):
      </div>
      <div class="grid grid-cols-2 gap-2">
        <button
          type="button"
          onclick={() => { selectedGender = 'm'; playClickSound(); }}
          class="p-2.5 rounded-xl border text-left transition-all cursor-pointer flex items-center gap-2.5 {selectedGender === 'm'
            ? 'bg-amber-950/40 border-amber-500/80 text-amber-300'
            : 'bg-[#141210]/60 border-[#2d2924] text-[#a39e95] hover:border-[#3d3831]'}"
        >
          <span class="text-lg">👨✈️</span>
          <div>
            <div class="text-xs font-bold text-[#f5f3ef]">Мужчина</div>
            <div class="text-[10px] text-[#a39e95]">Проводник ВСМ</div>
          </div>
        </button>

        <button
          type="button"
          onclick={() => { selectedGender = 'f'; playClickSound(); }}
          class="p-2.5 rounded-xl border text-left transition-all cursor-pointer flex items-center gap-2.5 {selectedGender === 'f'
            ? 'bg-amber-950/40 border-amber-500/80 text-amber-300'
            : 'bg-[#141210]/60 border-[#2d2924] text-[#a39e95] hover:border-[#3d3831]'}"
        >
          <span class="text-lg">👩✈️</span>
          <div>
            <div class="text-xs font-bold text-[#f5f3ef]">Девушка</div>
            <div class="text-[10px] text-[#a39e95]">Проводница ВСМ</div>
          </div>
        </button>
      </div>
    </div>

    <!-- Выбор квалификации -->
    <div class="w-full mb-4">
      <div class="text-[11px] font-semibold text-[#a39e95] uppercase tracking-wider mb-2 text-left">
        2. Квалификация сотрудника:
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
          <div class="text-[10px] text-[#a39e95] mt-0.5">Бизнес-класс • Опытный</div>
        </button>

        <button
          type="button"
          onclick={() => { selectedRole = 'trainee'; playClickSound(); }}
          class="p-2.5 rounded-xl border text-left transition-all cursor-pointer {selectedRole === 'trainee'
            ? 'bg-amber-950/40 border-amber-500/80 text-amber-300'
            : 'bg-[#141210]/60 border-[#2d2924] text-[#a39e95] hover:border-[#3d3831]'}"
        >
          <div class="text-xs font-bold text-[#f5f3ef]">Проводник-стажер</div>
          <div class="text-[10px] text-[#a39e95] mt-0.5">Низкие стартовые ЗУН</div>
        </button>
      </div>
    </div>

    <!-- Превью выбранного персонажа -->
    <div class="w-full p-3 rounded-xl bg-[#141210] border border-[#2d2924] mb-5 text-left flex items-center justify-between">
      <div>
        <div class="text-xs font-bold text-amber-300">{previewProfile.name}</div>
        <div class="text-[10px] text-[#a39e95] mt-0.5">{previewProfile.desc}</div>
      </div>
      <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
        {selectedGender === 'f' ? 'ЖЕН' : 'МУЖ'}
      </span>
    </div>

    <button
      onclick={handleLogin}
      disabled={isLoading}
      class="w-full py-3 px-5 rounded-xl bg-gradient-to-r from-amber-600 via-amber-500 to-yellow-500 hover:from-amber-500 hover:to-yellow-400 active:scale-[0.99] text-stone-950 font-bold text-xs sm:text-sm tracking-wide shadow-lg shadow-amber-500/20 border border-amber-400/40 transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
    >
      {#if isLoading}
        <span>Вход в систему...</span>
      {:else}
        <span>🚄 Войти как {previewProfile.name}</span>
      {/if}
    </button>
  </div>
</div>
