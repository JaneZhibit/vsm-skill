<script lang="ts">
  import { fade } from 'svelte/transition';
  import { trainWorld } from '../../stores/trainWorld.svelte';
  import { playClickSound, playErrorSound, playSuccessSound } from '../../utils/audio';

  let items = $state([
    { id: 'extinguisher', title: 'Огнетушитель (Пломба)', imgGood: '/assets/extinguisher_good.jpg', imgBad: '/assets/extinguisher_bad.jpg', isBroken: Math.random() > 0.6, userSelection: null as boolean | null },
    { id: 'toilet', title: 'Санитарный блок', imgGood: '/assets/toilet_good.jpg', imgBad: '/assets/toilet_bad.jpg', isBroken: Math.random() > 0.6, userSelection: null as boolean | null },
    { id: 'climate', title: 'Климат-контроль', imgGood: '/assets/climate_good.jpg', imgBad: '/assets/climate_bad.jpg', isBroken: Math.random() > 0.6, userSelection: null as boolean | null },
  ]);

  let currentIndex = $state(0);

  const currentItem = $derived(items[currentIndex]);

  function selectStatus(status: boolean) {
    items[currentIndex].userSelection = status;
    playClickSound();
    if (currentIndex < items.length - 1) {
      currentIndex++;
    }
  }

  function verify() {
    let hasError = false;
    let hasDefects = false;

    items.forEach(item => {
      const correctSelection = !item.isBroken;
      if (item.userSelection !== correctSelection) {
        hasError = true;
      }
      if (item.isBroken) {
        hasDefects = true;
      }
    });

    if (hasError) {
      playErrorSound();
      trainWorld.showToast('Ошибка проверки', 'Вы неверно оценили состояние вагона. Перепроверьте фото!');
    } else {
      playSuccessSound();
      if (hasDefects) {
        trainWorld.showToast('Найдены неисправности', 'Доложите ЛНП по рации для вызова ремонтной бригады!');
        trainWorld.setPreTripNeedsRadio(true);
      } else {
        trainWorld.showToast('Приемка завершена', 'Оборудование в идеальном состоянии. Вагон готов к рейсу.');
        trainWorld.completePreTrip();
      }
    }
  }
</script>

<!-- Модальное окно приемки жестко привязано к краям экрана -->
<div class="fixed inset-0 z-[120] bg-black/90 backdrop-blur-md flex flex-col md:items-center md:justify-center md:p-6" transition:fade={{duration: 200}}>

  <!-- Контейнер: на мобильных занимает 100% высоты (flex-1 min-h-0), на ПК выглядит как карточка -->
  <div class="flex-1 min-h-0 w-full md:flex-none md:h-auto md:max-h-[85vh] max-w-5xl bg-[#1a1816] md:rounded-2xl border-0 md:border border-[#3d3831] shadow-2xl flex flex-col md:flex-row overflow-hidden">

    <!-- 1. ФОТО-ОСМОТР (Компактный блок камеры сверху на мобильных) -->
    <div class="shrink-0 min-h-[200px] h-[32vh] max-h-[35vh] md:max-h-none md:h-auto md:flex-1 relative bg-[#0a0908] flex flex-col items-center justify-between p-2 sm:p-3 md:p-5 border-b md:border-b-0 md:border-r border-[#3d3831]">
      <div class="absolute top-2 left-2 sm:top-3 sm:left-3 bg-black/80 px-2.5 py-0.5 sm:py-1 rounded text-[10px] sm:text-xs text-amber-500 font-mono border border-amber-900/50 z-10">
        КАМЕРА: ОБЪЕКТ {currentIndex + 1}/3
      </div>

      <div class="flex-1 min-h-0 w-full flex items-center justify-center overflow-hidden py-1 sm:py-2">
        <img
          src={currentItem.isBroken ? currentItem.imgBad : currentItem.imgGood}
          alt={currentItem.title}
          class="max-w-full max-h-full object-contain drop-shadow-2xl transition-opacity duration-300"
          onerror={(e) => { const target = e.currentTarget as HTMLImageElement; target.src = '/assets/cabin.jpg'; }}
        />
      </div>

      <div class="shrink-0 flex items-center gap-2 sm:gap-3 bg-black/60 px-3 py-1.5 sm:py-2 rounded-xl border border-[#3d3831] w-full max-w-[280px] sm:max-w-[300px] justify-between">
        <button onclick={() => {if(currentIndex > 0) currentIndex--; playClickSound();}} class="text-[#a39e95] hover:text-white disabled:opacity-20 cursor-pointer p-1 font-bold text-sm" disabled={currentIndex === 0}>◀</button>
        <span class="text-[11px] sm:text-xs font-bold text-[#f5f3ef] text-center flex-1 truncate px-2">{currentItem.title}</span>
        <button onclick={() => {if(currentIndex < 2) currentIndex++; playClickSound();}} class="text-[#a39e95] hover:text-white disabled:opacity-20 cursor-pointer p-1 font-bold text-sm" disabled={currentIndex === 2}>▶</button>
      </div>
    </div>

    <!-- 2. ПЛАНШЕТ С ЧЕК-ЛИСТОМ -->
    <div class="flex-1 min-h-0 md:flex-none md:w-[380px] bg-[#fdfbf7] flex flex-col text-stone-900 relative">

      <!-- Шапка документа (Всегда сверху) -->
      <div class="shrink-0 px-4 py-3 sm:px-5 sm:py-4 border-b border-stone-300 bg-[#f4f0e6]">
        <div class="flex items-center gap-2 mb-1">
          <span class="w-4 h-4 sm:w-5 sm:h-5 bg-stone-900 text-white rounded flex items-center justify-center text-[9px] sm:text-[10px] font-bold">РЖД</span>
          <span class="text-[9px] sm:text-[10px] uppercase font-bold tracking-wider text-stone-500">ЛБ-34 (Приемка)</span>
        </div>
        <h2 class="font-black text-sm sm:text-base text-stone-800 leading-tight">Лист осмотра оборудования</h2>
      </div>

      <!-- Скроллируемая область списка (Теперь 100% скроллится на мобильных) -->
      <div class="flex-1 min-h-0 overflow-y-auto p-3 sm:p-5 flex flex-col gap-2.5 sm:gap-3.5 bg-[#fdfbf7] overscroll-contain pb-6">
        <p class="text-[10px] sm:text-xs text-stone-500 font-medium leading-snug">
          Отметьте состояние проверяемых узлов вагона перед отправлением:
        </p>

        {#each items as item, idx}
          <!-- svelte-ignore a11y_click_events_have_key_events -->
          <!-- svelte-ignore a11y_no_static_element_interactions -->
          <div onclick={() => { currentIndex = idx; playClickSound(); }} class="flex flex-col gap-2.5 p-3 sm:p-3.5 rounded-xl border-2 transition-all cursor-pointer shrink-0 {currentIndex === idx ? 'border-amber-500 bg-amber-50/80 shadow-sm' : 'border-stone-200 bg-white hover:border-stone-300'}">
            <div class="flex items-center justify-between">
              <div class="font-bold text-xs sm:text-sm text-stone-800">{idx + 1}. {item.title}</div>
              {#if item.userSelection !== null}
                <span class="text-[10px] font-bold px-1.5 py-0.5 rounded {item.userSelection ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">{item.userSelection ? 'Норма' : 'Брак'}</span>
              {/if}
            </div>

            <div class="flex gap-2 w-full">
              <button onclick={(e) => { e.stopPropagation(); currentIndex = idx; selectStatus(true); }} class="flex-1 py-2 sm:py-2.5 rounded-lg text-xs sm:text-sm font-bold border transition-all cursor-pointer {item.userSelection === true ? 'bg-emerald-500 text-white border-emerald-600 shadow-inner' : 'bg-stone-100 text-stone-600 border-stone-200 hover:bg-stone-200'}">✅ В норме</button>
              <button onclick={(e) => { e.stopPropagation(); currentIndex = idx; selectStatus(false); }} class="flex-1 py-2 sm:py-2.5 rounded-lg text-xs sm:text-sm font-bold border transition-all cursor-pointer {item.userSelection === false ? 'bg-rose-500 text-white border-rose-600 shadow-inner' : 'bg-stone-100 text-stone-600 border-stone-200 hover:bg-stone-200'}">❌ Брак</button>
            </div>
          </div>
        {/each}
      </div>

      <!-- Прикрепленный футер (Всегда виден снизу) -->
      <div class="shrink-0 p-3 sm:p-5 pb-[max(0.75rem,env(safe-area-inset-bottom))] border-t border-stone-300 bg-white shadow-[0_-4px_12px_rgba(0,0,0,0.06)]">
        <button onclick={verify} disabled={items.some(i => i.userSelection === null)} class="w-full py-3.5 rounded-xl font-bold text-xs sm:text-sm transition-all shadow-md cursor-pointer disabled:opacity-50 disabled:grayscale flex items-center justify-center gap-2 bg-stone-900 text-white hover:bg-stone-800 active:scale-[0.98]">
          <span>Подписать лист приемки ➔</span>
        </button>
      </div>
    </div>

  </div>
</div>