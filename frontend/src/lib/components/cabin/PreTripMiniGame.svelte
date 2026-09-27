<script lang="ts">
  import { fade } from 'svelte/transition';
  import { trainWorld } from '../../stores/trainWorld.svelte';
  import { playClickSound, playErrorSound, playSuccessSound } from '../../utils/audio';

  let items = $state([
    { id: 'extinguisher', title: 'Огнетушитель (Пломба)', imgGood: '/assets/extinguisher_good.jpg', imgBad: '/assets/extinguisher_bad.jpg', isBroken: false, userSelection: null as boolean | null },
    { id: 'toilet', title: 'Санитарный блок', imgGood: '/assets/toilet_good.jpg', imgBad: '/assets/toilet_bad.jpg', isBroken: false, userSelection: null as boolean | null },
    { id: 'climate', title: 'Климат-контроль', imgGood: '/assets/climate_good.jpg', imgBad: '/assets/climate_bad.jpg', isBroken: false, userSelection: null as boolean | null },
  ]);

  let currentIndex = $state(0);
  let isChecking = $state(false);

  $effect(() => {
    if (!isChecking) {
      isChecking = true;
      items.forEach(item => {
        item.isBroken = Math.random() > 0.6; // 40% шанс неисправности
      });
    }
  });

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

<!-- Используем fixed и z-[120], чтобы гарантированно перекрыть ВЕСЬ интерфейс -->
<div class="fixed inset-0 z-[120] bg-black/90 backdrop-blur-md flex items-center justify-center md:p-6" transition:fade={{duration: 200}}>

  <!-- На мобилке h-full w-full без скруглений, на ПК - аккуратная карточка -->
  <div class="w-full h-full md:h-[85vh] max-w-5xl bg-[#1a1816] md:rounded-2xl border-0 md:border border-[#3d3831] shadow-2xl flex flex-col md:flex-row overflow-hidden">

    <!-- ЛЕВАЯ ЧАСТЬ: ФОТО-ОСМОТР (Сверху на мобилках) -->
    <div class="h-[45vh] md:h-auto md:flex-1 relative bg-[#0a0908] flex flex-col items-center p-3 md:p-5 border-b md:border-b-0 md:border-r border-[#3d3831]">
      <div class="absolute top-3 left-3 bg-black/80 px-3 py-1 rounded text-[10px] sm:text-xs text-amber-500 font-mono border border-amber-900/50 z-10">
        КАМЕРА: ОБЪЕКТ {currentIndex + 1}/3
      </div>

      <!-- Картинка -->
      <div class="flex-1 w-full flex items-center justify-center overflow-hidden py-4">
        <img
          src={currentItem.isBroken ? currentItem.imgBad : currentItem.imgGood}
          alt={currentItem.title}
          class="max-w-full max-h-full object-contain drop-shadow-2xl transition-opacity duration-300"
          onerror={(e) => { const target = e.currentTarget as HTMLImageElement; target.src = '/assets/cabin.png'; }}
        />
      </div>

      <!-- Навигация фото (теперь не перекрывает картинку) -->
      <div class="shrink-0 flex items-center gap-3 bg-black/60 px-4 py-2.5 rounded-xl border border-[#3d3831] w-full max-w-[300px] justify-between">
        <button
          onclick={() => {if(currentIndex > 0) currentIndex--; playClickSound();}}
          class="text-[#a39e95] hover:text-white disabled:opacity-20 cursor-pointer p-1 font-bold text-sm"
          disabled={currentIndex === 0}>◀</button>
        <span class="text-xs font-bold text-[#f5f3ef] text-center flex-1 truncate px-2">{currentItem.title}</span>
        <button
          onclick={() => {if(currentIndex < 2) currentIndex++; playClickSound();}}
          class="text-[#a39e95] hover:text-white disabled:opacity-20 cursor-pointer p-1 font-bold text-sm"
          disabled={currentIndex === 2}>▶</button>
      </div>
    </div>

    <!-- ПРАВАЯ ЧАСТЬ: ПЛАНШЕТ С ЧЕК-ЛИСТОМ (Снизу на мобилках) -->
    <div class="flex-1 md:flex-none md:w-[380px] bg-[#fdfbf7] flex flex-col text-stone-900 relative">
      <div class="p-4 sm:p-5 border-b border-stone-300 bg-[#f4f0e6] shrink-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="w-5 h-5 bg-stone-900 text-white rounded flex items-center justify-center text-[10px] font-bold">РЖД</span>
          <span class="text-[10px] uppercase font-bold tracking-wider text-stone-500">ЛБ-34 (Приемка вагона)</span>
        </div>
        <h2 class="font-black text-base sm:text-lg text-stone-800 leading-tight">Лист осмотра оборудования</h2>
      </div>

      <div class="flex-1 overflow-y-auto p-4 sm:p-5 flex flex-col gap-3.5 bg-[#fdfbf7]">
        <p class="text-[11px] sm:text-xs text-stone-500 font-medium leading-snug">
          Отметьте состояние проверяемых узлов вагона перед отправлением:
        </p>

        {#each items as item, idx}
          <!-- svelte-ignore a11y_click_events_have_key_events -->
          <!-- svelte-ignore a11y_no_static_element_interactions -->
          <div
            onclick={() => { currentIndex = idx; playClickSound(); }}
            class="flex flex-col gap-2.5 p-3.5 rounded-xl border-2 transition-all cursor-pointer {currentIndex === idx ? 'border-amber-500 bg-amber-50 shadow-sm' : 'border-stone-200 bg-white hover:border-stone-300'}"
          >
            <div class="font-bold text-sm text-stone-800">{idx + 1}. {item.title}</div>

            <div class="flex gap-2 w-full">
              <button
                onclick={(e) => { e.stopPropagation(); currentIndex = idx; selectStatus(true); }}
                class="flex-1 py-2 sm:py-2.5 rounded-lg text-xs sm:text-sm font-bold border transition-all cursor-pointer {item.userSelection === true ? 'bg-emerald-500 text-white border-emerald-600 shadow-inner' : 'bg-stone-100 text-stone-500 border-stone-200 hover:bg-stone-200'}"
              >
                ✅ В норме
              </button>
              <button
                onclick={(e) => { e.stopPropagation(); currentIndex = idx; selectStatus(false); }}
                class="flex-1 py-2 sm:py-2.5 rounded-lg text-xs sm:text-sm font-bold border transition-all cursor-pointer {item.userSelection === false ? 'bg-rose-500 text-white border-rose-600 shadow-inner' : 'bg-stone-100 text-stone-500 border-stone-200 hover:bg-stone-200'}"
              >
                ❌ Брак
              </button>
            </div>
          </div>
        {/each}
      </div>

      <div class="p-4 sm:p-5 border-t border-stone-300 bg-white shrink-0">
        <button
          onclick={verify}
          disabled={items.some(i => i.userSelection === null)}
          class="w-full py-3.5 sm:py-4 rounded-xl font-bold text-sm transition-all shadow-lg cursor-pointer disabled:opacity-50 disabled:grayscale flex items-center justify-center gap-2 bg-stone-900 text-white hover:bg-stone-800 active:scale-[0.98]"
        >
          <span>Подписать лист приемки ➔</span>
        </button>
      </div>
    </div>

  </div>
</div>