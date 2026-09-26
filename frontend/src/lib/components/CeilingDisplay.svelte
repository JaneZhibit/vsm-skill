<script lang="ts">
  import { onMount } from 'svelte';
  import { fade } from 'svelte/transition';
  import { trainWorld } from '../stores/trainWorld.svelte';

  // 3 информационных экрана с ротацией каждые 4 секунды
  let currentScreen = $state<number>(0);

  onMount(() => {
    const interval = setInterval(() => {
      currentScreen = (currentScreen + 1) % 3;
    }, 4000);

    return () => {
      clearInterval(interval);
    };
  });

  const nextStationName = $derived.by(() => {
    const cp = trainWorld.nextCheckpoint;
    if (!cp) return 'Санкт-Петербург';
    return cp.checkpoint.label.replace(' (вокзал)', '').trim();
  });
</script>

<!-- Диегетическое потолочное информационное табло над дверью тамбура -->
<div class="ceiling-display select-none pointer-events-none" aria-live="polite">
  <!-- Светодиодная сетка (диодная текстура) -->
  <div class="led-grid-overlay"></div>

  <!-- Контент текущего информационного экрана -->
  <div class="screen-wrapper">
    {#if currentScreen === 0}
      <!-- Экран 1: Скорость и вагон -->
      <div in:fade={{ duration: 250 }} class="led-content">
        <span class="led-icon">🚄</span>
        <span class="led-text font-bold">{Math.round(trainWorld.speed)} км/ч</span>
        <span class="led-divider">•</span>
        <span class="led-text">Вг {trainWorld.wagonNumber} [{trainWorld.wagonType}]</span>
      </div>
    {:else if currentScreen === 1}
      <!-- Экран 2: Время и следующая станция -->
      <div in:fade={{ duration: 250 }} class="led-content">
        <span class="led-icon">🕒</span>
        <span class="led-text font-bold">{trainWorld.formattedTime}</span>
        <span class="led-divider">•</span>
        <span class="led-text">След: {nextStationName}</span>
      </div>
    {:else if currentScreen === 2}
      <!-- Экран 3: Климат в салоне и погода за бортом -->
      <div in:fade={{ duration: 250 }} class="led-content">
        <span class="led-icon">🌡️</span>
        <span class="led-text">Салон +{trainWorld.cabinTemperature}°C</span>
        <span class="led-divider">•</span>
        <span class="led-text">Борт +{trainWorld.outdoorTemperature}°C ({trainWorld.weatherCondition})</span>
      </div>
    {/if}
  </div>
</div>

<style>
  .ceiling-display {
    /* Точные координаты потолочного табло над дверью вагона (по cabin_aisle.png) */
    --display-top: 20.3%;
    --display-left: 43.95%;
    --display-width: 10.7%;
    --display-height: 2.25%;

    position: absolute;
    top: var(--display-top);
    left: var(--display-left);
    width: var(--display-width);
    height: var(--display-height);
    transform: translateZ(0);
    z-index: 15;

    background-color: #050505;
    border-radius: 2px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow:
      inset 0 0 4px rgba(0, 0, 0, 0.95),
      inset 0 1px 1px rgba(255, 255, 255, 0.05),
      0 0 8px rgba(245, 158, 11, 0.18);
    overflow: hidden;
    container-type: size;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  /* Текстура светодиодной матрицы (LED dot matrix) */
  .led-grid-overlay {
    position: absolute;
    inset: 0;
    z-index: 2;
    pointer-events: none;
    background-image: radial-gradient(rgba(0, 0, 0, 0.75) 1px, transparent 1px);
    background-size: 3px 3px;
    opacity: 0.5;
  }

  .screen-wrapper {
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1;
    padding: 0 4px;
  }

  .led-content {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.35em;
    white-space: nowrap;
    color: #f59e0b;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: clamp(5px, 4.6cqi, 8.5px);
    line-height: 1;
    letter-spacing: 0.02em;
    filter: drop-shadow(0 0 3px rgba(245, 158, 11, 0.65));
    text-shadow:
      0 0 2px rgba(245, 158, 11, 0.9),
      0 0 6px rgba(217, 119, 6, 0.5);
  }

  .led-icon {
    font-size: 0.85em;
    filter: none;
    opacity: 0.9;
  }

  .led-text {
    flex-shrink: 0;
  }

  /* Аутентичный мигающий разделитель диодного табло */
  .led-divider {
    color: #f59e0b;
    opacity: 0.85;
    animation: ledPulse 1s steps(1) infinite;
  }

  @keyframes ledPulse {
    0%, 100% {
      opacity: 0.95;
    }
    50% {
      opacity: 0.15;
    }
  }
</style>
