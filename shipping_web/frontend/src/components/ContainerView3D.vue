<template>
  <div class="container-3d">
    <div class="view-header">
      <h3>3D 적재 시각화</h3>
      <div class="utilization">
        <span class="util-item">
          <span class="util-label">부피 활용률</span>
          <span class="util-value" :class="utilClass(store.containerResult.volume_utilization_pct)">
            {{ store.containerResult.volume_utilization_pct }}%
          </span>
        </span>
        <span class="util-item">
          <span class="util-label">중량 활용률</span>
          <span class="util-value" :class="utilClass(store.containerResult.weight_utilization_pct)">
            {{ store.containerResult.weight_utilization_pct }}%
          </span>
        </span>
        <span class="util-item">
          <span class="util-label">배치</span>
          <span class="util-value">
            {{ store.containerResult.placed_cases.length }}
            <template v-if="store.containerResult.unplaced_cases.length">
              / 미배치 {{ store.containerResult.unplaced_cases.length }}
            </template>
          </span>
        </span>
      </div>
    </div>

    <div class="canvas-wrap" ref="canvasWrap">
      <canvas ref="canvasEl"></canvas>
    </div>

    <div class="legend">
      <span
        v-for="(color, cat) in usedCategories"
        :key="cat"
        class="legend-item"
      >
        <span class="legend-swatch" :style="{ background: color }"></span>
        {{ cat }}
      </span>
    </div>

    <CaseTooltip
      :caseData="tooltipCase"
      :x="tooltipX"
      :y="tooltipY"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { usePackingStore } from '../stores/packingStore.js'
import { CATEGORY_COLORS } from '../utils/colors.js'
import { ContainerScene } from '../utils/containerScene.js'
import CaseTooltip from './CaseTooltip.vue'

const store = usePackingStore()
const canvasEl = ref(null)
const canvasWrap = ref(null)
const tooltipCase = ref(null)
const tooltipX = ref(0)
const tooltipY = ref(0)

let sceneInstance = null

const usedCategories = computed(() => {
  if (!store.containerResult) return {}
  const cats = new Set(store.containerResult.placed_cases.map(c => c.category))
  const result = {}
  for (const cat of cats) {
    result[cat] = CATEGORY_COLORS[cat] || CATEGORY_COLORS.UNKNOWN
  }
  return result
})

function utilClass(pct) {
  if (pct >= 70) return 'util-high'
  if (pct >= 40) return 'util-mid'
  return 'util-low'
}

function renderScene() {
  if (!sceneInstance || !store.containerResult) return
  sceneInstance.clear()
  sceneInstance.drawContainer(store.containerResult.container_dims)
  sceneInstance.drawCases(store.containerResult.placed_cases)
}

onMounted(() => {
  if (!canvasEl.value) return
  sceneInstance = new ContainerScene(canvasEl.value)
  sceneInstance.onCaseClick = (data, x, y) => {
    tooltipCase.value = data
    tooltipX.value = x || 0
    tooltipY.value = y || 0
  }
  const wrap = canvasWrap.value
  if (wrap) {
    sceneInstance.resize(wrap.clientWidth, 500)
    const observer = new ResizeObserver(() => {
      sceneInstance.resize(wrap.clientWidth, 500)
    })
    observer.observe(wrap)
  }
  renderScene()
})

watch(() => store.containerResult, () => renderScene())

onBeforeUnmount(() => {
  if (sceneInstance) sceneInstance.dispose()
})
</script>

<style scoped>
.container-3d {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 16px;
  gap: 12px;
}
.view-header h3 { font-size: 16px; }
.utilization { display: flex; gap: 20px; }
.util-item { display: flex; flex-direction: column; align-items: center; }
.util-label { font-size: 11px; color: #888; }
.util-value { font-size: 16px; font-weight: 700; }
.util-high { color: #2e7d32; }
.util-mid { color: #f57f17; }
.util-low { color: #c62828; }
.canvas-wrap {
  width: 100%;
  height: 500px;
  border-radius: 8px;
  overflow: hidden;
  background: #f0f2f5;
}
.canvas-wrap canvas { width: 100%; height: 100%; display: block; }
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #555;
}
.legend-swatch {
  width: 14px;
  height: 14px;
  border-radius: 3px;
}
</style>
