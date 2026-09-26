<script lang="ts">
  import { fly } from 'svelte/transition';
  import { conductorState } from '../stores/conductorState.svelte';
  
  let ach = $derived(conductorState.achievementToast);
</script>

{#if ach}
  <div 
    transition:fly={{ y: 50, duration: 400, opacity: 0 }}
    class="fixed bottom-6 left-1/2 -translate-x-1/2 z-[200] pointer-events-none"
  >
    <div class="relative overflow-hidden bg-[#141210]/95 backdrop-blur-xl border-2 border-amber-400/80 rounded-2xl p-4 shadow-[0_10px_40px_rgba(245,158,11,0.3)] flex items-center gap-4 w-max max-w-[90vw]">
      <!-- Блики и свечение -->
      <div class="absolute inset-0 bg-gradient-to-r from-amber-500/10 via-transparent to-amber-500/10"></div>
      <div class="absolute -top-10 -left-10 w-20 h-20 bg-white/20 blur-2xl rounded-full"></div>
      
      <!-- Иконка достижения -->
      <div class="relative z-10 w-12 h-12 rounded-xl bg-gradient-to-tr from-amber-600 to-yellow-400 flex items-center justify-center text-2xl shadow-lg shadow-amber-500/40 border border-white/20">
        {ach.icon}
      </div>
      
      <!-- Текст -->
      <div class="relative z-10 flex flex-col">
        <span class="text-[10px] font-mono font-bold text-amber-400 uppercase tracking-widest mb-0.5">
          Новое достижение разблокировано
        </span>
        <span class="text-sm sm:text-base font-bold text-white leading-tight">
          {ach.title}
        </span>
        <span class="text-xs text-[#a39e95] mt-0.5 max-w-xs truncate">
          {ach.description}
        </span>
      </div>
    </div>
  </div>
{/if}
