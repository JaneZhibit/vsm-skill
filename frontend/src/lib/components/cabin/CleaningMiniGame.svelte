<script lang="ts">
  import { fade } from 'svelte/transition';
  import { trainWorld } from '../../stores/trainWorld.svelte';
  import { conductorState } from '../../stores/conductorState.svelte';
  import { playSuccessSound, playClickSound } from '../../utils/audio';

  interface Props {
    isTripFinished: boolean;
  }
  let { isTripFinished }: Props = $props();

  let activeZone = $state<'cabin' | 'toilet'>('cabin');

  let cabinCanvas = $state<HTMLCanvasElement | null>(null);
  let toiletCanvas = $state<HTMLCanvasElement | null>(null);

  let cabinCtx: CanvasRenderingContext2D | null = null;
  let toiletCtx: CanvasRenderingContext2D | null = null;

  let cabinProgress = $state<number>(0);
  let toiletProgress = $state<number>(0);

  let isCabinInit = false;
  let isToiletInit = false;

  let isErasing = false;
  let lastPoint: { x: number; y: number } | null = null;

  $effect(() => {
    const isArrival = conductorState.shiftPhase === 'arrival' || isTripFinished;
    if (isArrival) {
      if (cabinCanvas && !isCabinInit) {
        isCabinInit = true;
        cabinCtx = cabinCanvas.getContext('2d', { willReadFrequently: true });
        const img = new Image();
        img.src = '/assets/cabin_dirty.jpg'; // Ваш грязный слой салона (можно поменять на JPG, если нужно)
        img.onload = () => {
          if (cabinCanvas && cabinCtx) {
            cabinCanvas.width = img.naturalWidth || 1671;
            cabinCanvas.height = img.naturalHeight || 941;
            cabinCtx.drawImage(img, 0, 0, cabinCanvas.width, cabinCanvas.height);
          }
        };
      }
      if (toiletCanvas && !isToiletInit) {
        isToiletInit = true;
        toiletCtx = toiletCanvas.getContext('2d', { willReadFrequently: true });
        const img2 = new Image();
        img2.src = '/assets/toilet_bad.jpg'; // Новый грязный слой санузла
        img2.onload = () => {
          if (toiletCanvas && toiletCtx) {
            toiletCanvas.width = img2.naturalWidth || 1671;
            toiletCanvas.height = img2.naturalHeight || 941;
            toiletCtx.drawImage(img2, 0, 0, toiletCanvas.width, toiletCanvas.height);
          }
        };
      }
    } else {
      isCabinInit = false;
      isToiletInit = false;
      cabinProgress = 0;
      toiletProgress = 0;
      activeZone = 'cabin';
    }
  });

  $effect(() => {
    // Подсчет общего прогресса: среднее между салоном и туалетом
    const total = (cabinProgress + toiletProgress) / 2;
    const wasDone = trainWorld.cleaningProgress >= 70;
    trainWorld.cleaningProgress = total;

    if (total >= 70 && !wasDone) {
      playSuccessSound();
      trainWorld.showToast('Уборка завершена!', 'Вагон и санузел сияют чистотой.');
    }
  });

  function getPointerPos(e: MouseEvent | TouchEvent, canvas: HTMLCanvasElement) {
    const rect = canvas.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
      x: (clientX - rect.left) * scaleX,
      y: (clientY - rect.top) * scaleY
    };
  }

  function startErasing(e: MouseEvent | TouchEvent) {
    isErasing = true;
    const canvas = activeZone === 'cabin' ? cabinCanvas : toiletCanvas;
    if (canvas) {
      lastPoint = getPointerPos(e, canvas);
      erase(e);
    }
  }

  function stopErasing() {
    if (isErasing) {
      isErasing = false;
      lastPoint = null;
      checkCleaningProgress(activeZone);
    }
  }

  function erase(e: MouseEvent | TouchEvent) {
    if (!isErasing) return;
    const canvas = activeZone === 'cabin' ? cabinCanvas : toiletCanvas;
    const ctx = activeZone === 'cabin' ? cabinCtx : toiletCtx;
    if (!ctx || !canvas) return;

    const currentPoint = getPointerPos(e, canvas);

    ctx.globalCompositeOperation = 'destination-out';
    // Для санузла делаем губку поменьше, чтобы было интереснее тереть
    ctx.lineWidth = activeZone === 'toilet' ? 100 : 160;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    ctx.beginPath();
    if (lastPoint) {
      ctx.moveTo(lastPoint.x, lastPoint.y);
      ctx.lineTo(currentPoint.x, currentPoint.y);
      ctx.stroke();
    } else {
      ctx.arc(currentPoint.x, currentPoint.y, activeZone === 'toilet' ? 50 : 80, 0, Math.PI * 2);
      ctx.fill();
    }
    lastPoint = currentPoint;
  }

  function checkCleaningProgress(zone: 'cabin' | 'toilet') {
    const canvas = zone === 'cabin' ? cabinCanvas : toiletCanvas;
    const ctx = zone === 'cabin' ? cabinCtx : toiletCtx;
    if (!ctx || !canvas) return;

    const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imgData.data;
    let transparentPixels = 0;
    const totalSampled = data.length / 16;

    for (let i = 3; i < data.length; i += 16) {
      if (data[i] < 128) transparentPixels++;
    }

    const progress = Math.min(100, (transparentPixels / totalSampled) * 100);
    if (zone === 'cabin') cabinProgress = progress;
    else toiletProgress = progress;
  }
</script>

{#if conductorState.shiftPhase === 'arrival' || isTripFinished}
  <!-- Обертка игры на весь экран вагона, перехватывающая клики -->
  <div class="absolute inset-0 z-[22] bg-black" transition:fade={{ duration: 300 }}>

    <!-- Переключатель зон сверху -->
    <div class="absolute top-4 left-1/2 -translate-x-1/2 z-30 flex gap-2 p-1.5 bg-[#141210]/90 backdrop-blur-md rounded-xl border border-[#3d3831] shadow-2xl">
      <button
        onclick={() => { activeZone = 'cabin'; playClickSound(); }}
        class="px-4 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer {activeZone === 'cabin' ? 'bg-amber-600 text-stone-950 shadow-md' : 'text-[#a39e95] hover:text-white'}"
      >
        🛋️ Салон ({Math.round(cabinProgress)}%)
      </button>
      <button
        onclick={() => { activeZone = 'toilet'; playClickSound(); }}
        class="px-4 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer {activeZone === 'toilet' ? 'bg-amber-600 text-stone-950 shadow-md' : 'text-[#a39e95] hover:text-white'}"
      >
        🚻 Санузел ({Math.round(toiletProgress)}%)
      </button>
    </div>

    {#if trainWorld.cleaningProgress < 70}
      <div class="absolute top-16 mt-2 left-1/2 -translate-x-1/2 z-[30] bg-stone-900/90 text-amber-400 border border-amber-500/40 px-6 py-2 rounded-full font-bold shadow-2xl backdrop-blur animate-pulse pointer-events-none text-xs flex items-center gap-2">
        <span>🧼</span>
        <span>Сотрите грязь и мусор губкой: {Math.round(trainWorld.cleaningProgress)}% / 70%</span>
      </div>
    {/if}

    <!-- ЗОНА 1: САЛОН -->
    <div class="absolute inset-0" style="display: {activeZone === 'cabin' ? 'block' : 'none'}">
      <!-- Чистый фон салона из основной сцены -->
      <img src="/assets/cabin.jpg" alt="Чистый салон" class="w-full h-full object-cover pointer-events-none" />
      <canvas
        bind:this={cabinCanvas}
        class="absolute inset-0 w-full h-full touch-none cursor-crosshair"
        onmousedown={startErasing}
        onmousemove={erase}
        onmouseup={stopErasing}
        onmouseleave={stopErasing}
        ontouchstart={startErasing}
        ontouchmove={erase}
        ontouchend={stopErasing}
      ></canvas>
    </div>

    <!-- ЗОНА 2: САНУЗЕЛ -->
    <div class="absolute inset-0" style="display: {activeZone === 'toilet' ? 'block' : 'none'}">
      <!-- Чистый фон санузла -->
      <img src="/assets/toilet_good.jpg" alt="Чистый санузел" class="w-full h-full object-cover pointer-events-none" />
      <canvas
        bind:this={toiletCanvas}
        class="absolute inset-0 w-full h-full touch-none cursor-crosshair"
        onmousedown={startErasing}
        onmousemove={erase}
        onmouseup={stopErasing}
        onmouseleave={stopErasing}
        ontouchstart={startErasing}
        ontouchmove={erase}
        ontouchend={stopErasing}
      ></canvas>
    </div>
  </div>
{/if}