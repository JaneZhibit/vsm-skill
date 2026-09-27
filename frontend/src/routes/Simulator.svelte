<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import TrainCabin from '../lib/components/cabin/TrainCabin.svelte';
  import { startAmbient, stopAmbient } from '../lib/utils/audio';
  import { trainAudio } from '../lib/stores/trainAudio.svelte';
  import { cabinState } from '../lib/stores/cabinState.svelte';

  onMount(() => {
    trainAudio.isAudioMuted = false; // Принудительно убеждаемся, что звук включен
    startAmbient();
    cabinState.loadCabinManifest();
  });

  onDestroy(() => {
    stopAmbient();
  });
</script>

<div class="h-full w-full relative overflow-hidden flex flex-col">
  <TrainCabin />
</div>