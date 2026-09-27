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

  // Инициализируем случайные поломки при старте
  $effect(() => {
    if (!isChecking) {
      isChecking = true;
      items.forEach(item => {
        item.isBroken = Math.random() > 0.6; // 40% шанс неисправности на каждый элемент
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
      // true = ОК (Галочка), false = ПРОБЛЕМА (Крестик)
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

<div class="absolute inset-0 z-[40] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6" transition:fade={{duration: 200}}>
  <div class="w-full max-w-5xl h-[85vh] bg-[#1a1816] rounded-2xl border border-[#3d3831] shadow-2xl flex flex-col md:flex-row overflow-hidden">

    <!-- ЛЕВАЯ ЧАСТЬ: ФОТО-ОСМОТР -->
    <div class="flex-1 relative bg-black flex flex-col items-center justify-center p-4">
      <div class="absolute top-4 left-4 bg-black/60 px-3 py-1 rounded text-xs text-stone-400 font-mono border border-stone-800 z-10">
        КАМЕРА: ОБЪЕКТ {currentIndex + 1}/3
      </div>

      <div class="w-full h-full relative flex items-center justify-center">
        <!-- Показываем картинку в зависимости от того, сломано или нет -->
        <img
          src={currentItem.isBroken ? currentItem.imgBad : currentItem.imgGood}
          alt={currentItem.title}
          class="max-w-full max-h-full object-contain rounded-lg shadow-2xl transition-opacity duration-300"
          onerror={(e) => { const target = e.currentTarget as HTMLImageElement; target.src = '/assets/cabin.png'; }}
        />
      </div>

      <!-- Навигация фото -->
      <div class="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-4 bg-black/80 px-4 py-2 rounded-full border border-[#3d3831]">
        <button
          onclick={() => {if(currentIndex > 0) currentIndex--; playClickSound();}}
          class="text-stone-300 hover:text-white px-2 disabled:opacity-30 cursor-pointer"
          disabled={currentIndex === 0}>◀ Пред</button>
        <span class="text-xs font-bold text-amber-500 w-24 text-center">{currentItem.title}</span>
        <button
          onclick={() => {if(currentIndex < 2) currentIndex++; playClickSound();}}
          class="text-stone-300 hover:text-white px-2 disabled:opacity-30 cursor-pointer"
          disabled={currentIndex === 2}>След ▶</button>
      </div>
    </div>

    <!-- ПРАВАЯ ЧАСТЬ: ПЛАНШЕТ С ЧЕК-ЛИСТОМ -->
    <div class="w-full md:w-[350px] bg-[#fdfbf7] flex flex-col text-stone-900 border-l border-[#3d3831]">
      <div class="p-5 border-b border-stone-300 bg-[#f4f0e6]">
        <div class="flex items-center gap-2 mb-1">
          <span class="w-5 h-5 bg-stone-900 text-white rounded flex items-center justify-center text-xs font-bold">РЖД</span>
          <span class="text-[10px] uppercase font-bold tracking-wider text-stone-500">ЛБ-34 (Приемка вагона)</span>
        </div>
        <h2 class="font-black text-lg text-stone-800">Лист осмотра оборудования</h2>
      </div>

      <div class="flex-1 p-5 flex flex-col gap-4 overflow-y-auto">
        <p class="text-xs text-stone-600 font-medium mb-2">Отметьте состояние проверяемых узлов вагона перед отправлением:</p>

        {#each items as item, idx}
          <!-- svelte-ignore a11y_click_events_have_key_events -->
          <!-- svelte-ignore a11y_no_static_element_interactions -->
          <div
            onclick={() => currentIndex = idx}
            class="flex flex-col gap-2 p-3 rounded-lg border-2 text-left transition-all cursor-pointer {currentIndex === idx ? 'border-amber-500 bg-amber-50' : 'border-stone-200 bg-white hover:border-stone-300'}"
          >
            <div class="font-bold text-sm text-stone-800">{idx + 1}. {item.title}</div>

            <div class="flex gap-2 w-full mt-1">
              <button
                onclick={(e) => { e.stopPropagation(); currentIndex = idx; selectStatus(true); }}
                class="flex-1 py-1.5 rounded text-sm font-bold border transition-all cursor-pointer {item.userSelection === true ? 'bg-emerald-500 text-white border-emerald-600 shadow-inner' : 'bg-stone-100 text-stone-400 border-stone-200 hover:bg-stone-200'}"
              >
                ✅ В норме
              </button>
              <button
                onclick={(e) => { e.stopPropagation(); currentIndex = idx; selectStatus(false); }}
                class="flex-1 py-1.5 rounded text-sm font-bold border transition-all cursor-pointer {item.userSelection === false ? 'bg-rose-500 text-white border-rose-600 shadow-inner' : 'bg-stone-100 text-stone-400 border-stone-200 hover:bg-stone-200'}"
              >
                ❌ Брак
              </button>
            </div>
          </div>
        {/each}
      </div>

      <div class="p-5 border-t border-stone-300 bg-white">
        <button
          onclick={verify}
          disabled={items.some(i => i.userSelection === null)}
          class="w-full py-3.5 rounded-xl font-bold text-sm transition-all shadow-md cursor-pointer disabled:opacity-50 disabled:grayscale flex items-center justify-center gap-2 bg-stone-900 text-white hover:bg-stone-800"
        >
          <span>Подписать лист приемки ➔</span>
        </button>
      </div>
    </div>

  </div>
</div>