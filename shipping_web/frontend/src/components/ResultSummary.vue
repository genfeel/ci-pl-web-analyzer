<template>
  <div class="summary">
    <div class="summary-header">
      <h2>분석 결과</h2>
      <span class="filename">{{ store.packingResult.filename }}</span>
    </div>

    <div class="card-grid">
      <div class="card">
        <div class="card-label">총 케이스</div>
        <div class="card-value">{{ store.packingResult.total_cases }}</div>
      </div>
      <div class="card">
        <div class="card-label">총 수량</div>
        <div class="card-value">{{ store.packingResult.total_quantity }}</div>
      </div>
      <div class="card">
        <div class="card-label">순중량 (kg)</div>
        <div class="card-value">{{ store.packingResult.total_net_weight.toFixed(2) }}</div>
      </div>
      <div class="card">
        <div class="card-label">총중량 (kg)</div>
        <div class="card-value">{{ store.packingResult.total_gross_weight.toFixed(2) }}</div>
      </div>
      <div class="card">
        <div class="card-label">CBM</div>
        <div class="card-value">{{ store.packingResult.total_cbm.toFixed(3) }}</div>
      </div>
      <div class="card" :class="store.validation.passed ? 'card-pass' : 'card-fail'">
        <div class="card-label">검증 상태</div>
        <div class="card-value">{{ store.validation.passed ? 'PASS' : 'FAIL' }}</div>
      </div>
    </div>

    <div v-if="store.validation.errors.length || store.validation.warnings.length" class="validation-details">
      <div v-for="err in store.validation.errors" :key="err" class="v-error">{{ err }}</div>
      <div v-for="warn in store.validation.warnings" :key="warn" class="v-warn">{{ warn }}</div>
    </div>

    <div class="category-badges">
      <span
        v-for="cat in store.categorySummary"
        :key="cat.category"
        class="badge"
        :style="{ background: getCategoryColor(cat.category) }"
      >
        {{ cat.category }} ({{ cat.case_count }}C / {{ cat.total_quantity }}pcs)
      </span>
    </div>

    <button class="download-btn" @click="store.downloadPL()">PL Excel 다운로드</button>
  </div>
</template>

<script setup>
import { usePackingStore } from '../stores/packingStore.js'
import { getCategoryColor } from '../utils/colors.js'

const store = usePackingStore()
</script>

<style scoped>
.summary {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.summary-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 20px;
}
.summary-header h2 { font-size: 18px; }
.filename { font-size: 13px; color: #888; }
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.card {
  background: #f8f9fb;
  border-radius: 8px;
  padding: 14px;
  text-align: center;
}
.card-label { font-size: 12px; color: #888; margin-bottom: 6px; }
.card-value { font-size: 20px; font-weight: 700; }
.card-pass { background: #e8f5e9; }
.card-pass .card-value { color: #2e7d32; }
.card-fail { background: #ffebee; }
.card-fail .card-value { color: #c62828; }
.validation-details {
  margin-bottom: 16px;
  font-size: 13px;
}
.v-error {
  color: #c62828;
  padding: 4px 0;
}
.v-error::before { content: '\2717 '; }
.v-warn {
  color: #e65100;
  padding: 4px 0;
}
.v-warn::before { content: '\26A0 '; }
.category-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}
.badge {
  color: #fff;
  padding: 4px 12px;
  border-radius: 14px;
  font-size: 12px;
  font-weight: 600;
}
.download-btn {
  padding: 10px 24px;
  background: #43a047;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}
.download-btn:hover { background: #388e3c; }
</style>
