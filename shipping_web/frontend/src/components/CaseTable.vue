<template>
  <div class="case-table-wrap">
    <h3>케이스 상세</h3>
    <table class="case-table">
      <thead>
        <tr>
          <th class="col-expand"></th>
          <th>Case</th>
          <th>Type</th>
          <th>Category</th>
          <th>Items</th>
          <th>Qty</th>
          <th>N.W (kg)</th>
          <th>G.W (kg)</th>
          <th>Dims (mm)</th>
          <th>CBM</th>
          <th class="col-reason">Reason</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="c in store.cases" :key="c.case_no">
          <tr class="case-row" @click="toggle(c.case_no)">
            <td class="col-expand">{{ expanded.has(c.case_no) ? '▼' : '▶' }}</td>
            <td>{{ c.case_no }}</td>
            <td>{{ c.case_type }}</td>
            <td>
              <span class="cat-badge" :style="{ background: getCategoryColor(c.category) }">
                {{ c.category }}
              </span>
            </td>
            <td>{{ c.items.length }}</td>
            <td>{{ c.total_quantity }}</td>
            <td>{{ c.net_weight.toFixed(2) }}</td>
            <td>{{ c.gross_weight.toFixed(2) }}</td>
            <td class="dims">{{ formatDims(c.dimensions) }}</td>
            <td>{{ c.cbm.toFixed(3) }}</td>
            <td class="col-reason reason-cell">{{ c.reason }}</td>
          </tr>
          <tr v-if="expanded.has(c.case_no)" class="detail-row">
            <td colspan="11">
              <table class="item-table">
                <thead>
                  <tr>
                    <th>Description</th>
                    <th>Model</th>
                    <th>Qty</th>
                    <th>N.W (kg)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, idx) in c.items" :key="idx">
                    <td>{{ item.description }}</td>
                    <td>{{ item.model_number }}</td>
                    <td>{{ item.quantity }}</td>
                    <td>{{ item.net_weight.toFixed(2) }}</td>
                  </tr>
                </tbody>
              </table>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { usePackingStore } from '../stores/packingStore.js'
import { getCategoryColor } from '../utils/colors.js'

const store = usePackingStore()
const expanded = ref(new Set())

function toggle(caseNo) {
  if (expanded.value.has(caseNo)) {
    expanded.value.delete(caseNo)
  } else {
    expanded.value.add(caseNo)
  }
  expanded.value = new Set(expanded.value)
}

function formatDims(dims) {
  return dims.map(d => Math.round(d)).join(' x ')
}
</script>

<style scoped>
.case-table-wrap {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  overflow-x: auto;
}
.case-table-wrap h3 { margin-bottom: 16px; font-size: 16px; }
.case-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.case-table th {
  background: #f5f6f8;
  padding: 10px 8px;
  text-align: center;
  font-weight: 600;
  border-bottom: 2px solid #e0e0e0;
  white-space: nowrap;
}
.case-table td {
  padding: 8px;
  text-align: center;
  border-bottom: 1px solid #eee;
}
.col-expand { width: 28px; cursor: pointer; }
.col-reason { min-width: 200px; text-align: left !important; }
.reason-cell {
  text-align: left !important;
  background: #fffde7;
  font-weight: 500;
}
.case-row { cursor: pointer; transition: background 0.15s; }
.case-row:hover { background: #f5f8ff; }
.dims { font-family: monospace; font-size: 12px; white-space: nowrap; }
.cat-badge {
  color: #fff;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}
.detail-row td {
  padding: 0 8px 12px 40px;
  background: #fafbfc;
}
.item-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  margin-top: 8px;
}
.item-table th {
  background: #eef1f5;
  padding: 6px 8px;
  text-align: left;
  font-weight: 600;
}
.item-table td {
  padding: 5px 8px;
  border-bottom: 1px solid #eee;
  text-align: left;
}
</style>
