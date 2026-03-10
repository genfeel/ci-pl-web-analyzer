<template>
  <div v-if="caseData" class="tooltip" :style="tooltipStyle">
    <div class="tooltip-header">
      <span class="tooltip-case">Case {{ caseData.case_no }}</span>
      <span class="tooltip-badge" :style="{ background: getCategoryColor(caseData.category) }">
        {{ caseData.category }}
      </span>
    </div>
    <div class="tooltip-body">
      <div class="tooltip-row">
        <span class="label">Dims:</span>
        <span>{{ formatDims(caseData.dimensions) }} mm</span>
      </div>
      <div class="tooltip-row">
        <span class="label">G.W:</span>
        <span>{{ caseData.gross_weight }} kg</span>
      </div>
      <div class="tooltip-row">
        <span class="label">Layer:</span>
        <span>{{ caseData.layer_index + 1 }}</span>
      </div>
      <div class="tooltip-row">
        <span class="label">Rotated:</span>
        <span>{{ caseData.rotated ? 'Yes' : 'No' }}</span>
      </div>
      <div v-if="caseData.reason" class="tooltip-reason">
        <span class="label">Reason:</span>
        <span class="reason-text">{{ caseData.reason }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getCategoryColor } from '../utils/colors.js'

const props = defineProps({
  caseData: { type: Object, default: null },
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 },
})

const tooltipStyle = computed(() => ({
  left: props.x + 16 + 'px',
  top: props.y - 10 + 'px',
}))

function formatDims(dims) {
  return dims.map(d => Math.round(d)).join(' x ')
}
</script>

<style scoped>
.tooltip {
  position: fixed;
  z-index: 1000;
  background: #fff;
  border-radius: 8px;
  padding: 12px 16px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.18);
  min-width: 200px;
  pointer-events: none;
}
.tooltip-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}
.tooltip-case { font-weight: 700; font-size: 14px; }
.tooltip-badge {
  color: #fff;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}
.tooltip-body { font-size: 12px; }
.tooltip-row {
  display: flex;
  justify-content: space-between;
  padding: 2px 0;
}
.label { color: #888; font-weight: 500; }
.tooltip-reason {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid #eee;
}
.reason-text {
  color: #e65100;
  font-weight: 600;
}
</style>
