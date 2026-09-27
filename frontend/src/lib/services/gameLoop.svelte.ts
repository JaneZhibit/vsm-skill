// frontend/src/lib/services/gameLoop.svelte.ts
import { trainWorld } from '../stores/trainWorld.svelte';

export class GameLoopService {
  private lastFrameTime = 0;
  private animationFrameId: number | null = null;

  public start() {
    if (typeof window !== 'undefined') {
      const win = window as any;
      if (win.__vsm_raf_id) {
        cancelAnimationFrame(win.__vsm_raf_id);
        win.__vsm_raf_id = null;
      }
      this.lastFrameTime = performance.now();

      const loop = (timestamp: number) => {
        const deltaSec = Math.min((timestamp - this.lastFrameTime) / 1000, 0.1);
        this.lastFrameTime = timestamp;

        // Вызываем основную логику мира
        trainWorld.tick(deltaSec);

        this.animationFrameId = requestAnimationFrame(loop);
        win.__vsm_raf_id = this.animationFrameId;
      };

      this.animationFrameId = requestAnimationFrame(loop);
      win.__vsm_raf_id = this.animationFrameId;
    }
  }

  public stop() {
    if (typeof window !== 'undefined') {
      const win = window as any;
      if (this.animationFrameId !== null) {
        cancelAnimationFrame(this.animationFrameId);
        this.animationFrameId = null;
      }
      if (win.__vsm_raf_id) {
        cancelAnimationFrame(win.__vsm_raf_id);
        win.__vsm_raf_id = null;
      }
    }
  }
}

export const gameLoop = new GameLoopService();