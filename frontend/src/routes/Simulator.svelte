<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import TrainCabin from '../lib/components/TrainCabin.svelte';
  import { startAmbient, stopAmbient } from '../lib/utils/audio';
  import { trainWorld } from '../lib/stores/trainWorld.svelte';

  onMount(() => {
    trainWorld.isAudioMuted = false;
    startAmbient();
    trainWorld.loadCabinManifest();
  });

  onDestroy(() => {
    stopAmbient();
  });
</script>

<div class="h-full w-full relative overflow-hidden flex flex-col">
  <TrainCabin />
</div>
