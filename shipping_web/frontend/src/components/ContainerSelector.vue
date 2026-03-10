<template>
  <div class="container-selector">
    <h3>컨테이너 적재 시뮬레이션</h3>
    <div class="options">
      <label
        v-for="opt in options"
        :key="opt.value"
        class="option"
        :class="{ selected: store.selectedContainerType === opt.value }"
      >
        <input
          type="radio"
          :value="opt.value"
          v-model="store.selectedContainerType"
        />
        <div class="option-info">
          <span class="option-label">{{ opt.label }}</span>
          <span class="option-desc">{{ opt.desc }}</span>
        </div>
      </label>
    </div>
    <button
      class="simulate-btn"
      :disabled="store.loading"
      @click="store.simulateContainer(store.selectedContainerType)"
    >
      {{ store.loading ? '시뮬레이션 중...' : '적재 시뮬레이션 실행' }}
    </button>
  </div>
</template>

<script setup>
import { usePackingStore } from '../stores/packingStore.js'

const store = usePackingStore()

const options = [
  { value: '20ft', label: "20' Container", desc: '5,898 x 2,352 x 2,393 mm / 21.77t' },
  { value: '40ft', label: "40' Container", desc: '12,032 x 2,352 x 2,393 mm / 26.68t' },
  { value: '40ft_hc', label: "40' HC Container", desc: '12,032 x 2,352 x 2,698 mm / 26.46t' },
]
</script>

<style scoped>
.container-selector {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.container-selector h3 { margin-bottom: 16px; font-size: 16px; }
.options { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
.option {
  flex: 1;
  min-width: 180px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.option.selected { border-color: #2196F3; background: #e3f2fd; }
.option input { display: none; }
.option-label { font-weight: 600; display: block; }
.option-desc { font-size: 11px; color: #888; display: block; margin-top: 2px; }
.simulate-btn {
  padding: 10px 28px;
  background: #1565c0;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}
.simulate-btn:hover:not(:disabled) { background: #0d47a1; }
.simulate-btn:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
