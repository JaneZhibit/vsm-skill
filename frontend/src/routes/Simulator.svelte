<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import TrainCabin from '../lib/components/cabin/TrainCabin.svelte';
  import { startAmbient, stopAmbient } from '../lib/utils/audio';
  import { trainAudio } from '../lib/stores/trainAudio.svelte';
  import { cabinState } from '../lib/stores/cabinState.svelte';
  import { physicsState } from '../lib/stores/trainPhysics.svelte';

  onMount(() => {
    trainAudio.isAudioMuted = false; // Принудительно убеждаемся, что звук включен
    physicsState.isPaused = false;
    startAmbient();
    cabinState.loadCabinManifest();
  });

  onDestroy(() => {
    stopAmbient();
    physicsState.isPaused = true;
    trainAudio.fadeOutCurrentAnnouncement(100);
    trainAudio.stopEventAmbient();
  });
</script>

<div class="h-full w-full relative overflow-hidden flex flex-col">
  <TrainCabin />
</div>