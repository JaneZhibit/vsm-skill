<script lang="ts">
  import { trainWorld } from '../stores/trainWorld.svelte';

  const CX = 140;
  const CY = 120;
  const R = 65;

  const levels = [25, 50, 75, 100];

  let pNorth = $derived({
    x: CX,
    y: CY - (Math.max(0, Math.min(100, trainWorld.skills.safety_tech)) / 100) * R,
  });

  let pEast = $derived({
    x: CX + (Math.max(0, Math.min(100, trainWorld.skills.service_psychology)) / 100) * R,
    y: CY,
  });

  let pSouth = $derived({
    x: CX,
    y: CY + (Math.max(0, Math.min(100, trainWorld.skills.routine_discipline)) / 100) * R,
  });

  let pWest = $derived({
    x: CX - (Math.max(0, Math.min(100, trainWorld.skills.first_aid)) / 100) * R,
    y: CY,
  });

  let polygonPoints = $derived(
    `${pNorth.x.toFixed(1)},${pNorth.y.toFixed(1)} ${pEast.x.toFixed(1)},${pEast.y.toFixed(1)} ${pSouth.x.toFixed(1)},${pSouth.y.toFixed(1)} ${pWest.x.toFixed(1)},${pWest.y.toFixed(1)}`
  );
</script>

<div class="w-full flex items-center justify-center select-none py-1">
  <svg viewBox="0 0 280 240" class="w-[280px] h-[240px] block overflow-visible">
    <!-- Сетка -->
    {#each levels as lvl}
      {@const r = (lvl / 100) * R}
      <polygon
        points="{CX},{CY - r} {CX + r},{CY} {CX},{CY + r} {CX - r},{CY}"
        fill={lvl === 100 ? 'rgba(30, 26, 22, 0.4)' : 'none'}
        stroke="#2d2924"
        stroke-width={lvl === 100 ? '1.5' : '1'}
      />
    {/each}

    <!-- Направляющие оси -->
    <line x1={CX} y1={CY - R} x2={CX} y2={CY + R} stroke="#2d2924" stroke-width="1" />
    <line x1={CX - R} y1={CY} x2={CX + R} y2={CY} stroke="#2d2924" stroke-width="1" />

    <!-- Заполненная область навыков -->
    <polygon
      points={polygonPoints}
      fill="rgba(245, 158, 11, 0.2)"
      stroke="#f59e0b"
      stroke-width="2"
    />

    <!-- Точки на осях -->
    <circle cx={pNorth.x} cy={pNorth.y} r="3.5" fill="#f59e0b" />
    <circle cx={pEast.x} cy={pEast.y} r="3.5" fill="#f59e0b" />
    <circle cx={pSouth.x} cy={pSouth.y} r="3.5" fill="#f59e0b" />
    <circle cx={pWest.x} cy={pWest.y} r="3.5" fill="#f59e0b" />

    <!-- Компактные подписи без лишней шелухи -->
    <text x={CX} y="32" text-anchor="middle" font-size="10" fill="#a39e95" font-weight="600">
      Безопасность
    </text>
    <text x="240" y="124" text-anchor="middle" font-size="10" fill="#a39e95" font-weight="600">
      Сервис
    </text>
    <text x={CX} y="210" text-anchor="middle" font-size="10" fill="#a39e95" font-weight="600">
      Регламент
    </text>
    <text x="40" y="124" text-anchor="middle" font-size="10" fill="#a39e95" font-weight="600">
      Первая помощь
    </text>
  </svg>
</div>
