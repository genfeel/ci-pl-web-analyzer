<template>
  <div class="app">
    <header class="app-header">
      <h1>Shipping Document Analyzer</h1>
      <span class="subtitle">CI → PL 변환 및 컨테이너 적재 시뮬레이션</span>
      <button v-if="store.packingResult" class="reset-btn" @click="store.reset()">
        새 파일 분석
      </button>
    </header>

    <main class="app-main">
      <div v-if="store.error" class="error-banner">
        {{ store.error }}
        <button @click="store.error = null">닫기</button>
      </div>

      <!-- Step 1: 파일 업로드 -->
      <FileUpload v-if="!store.packingResult" />

      <!-- Step 2: 분석 결과 -->
      <template v-if="store.packingResult">
        <ResultSummary />
        <CaseTable />

        <!-- Step 3: 컨테이너 시뮬레이션 -->
        <ContainerSelector />

        <!-- Step 4: 3D 시각화 -->
        <ContainerView3D v-if="store.containerResult" />
      </template>
    </main>
  </div>
</template>

<script setup>
import { usePackingStore } from './stores/packingStore.js'
import FileUpload from './components/FileUpload.vue'
import ResultSummary from './components/ResultSummary.vue'
import CaseTable from './components/CaseTable.vue'
import ContainerSelector from './components/ContainerSelector.vue'
import ContainerView3D from './components/ContainerView3D.vue'

const store = usePackingStore()
</script>

<style>
.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
.app-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}
.app-header h1 { font-size: 22px; color: #1a237e; }
.subtitle { font-size: 13px; color: #888; }
.reset-btn {
  margin-left: auto;
  padding: 6px 16px;
  background: #e0e0e0;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}
.reset-btn:hover { background: #bdbdbd; }
.app-main {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.error-banner {
  background: #ffebee;
  color: #c62828;
  padding: 12px 16px;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}
.error-banner button {
  background: none;
  border: none;
  color: #c62828;
  font-weight: 600;
  cursor: pointer;
  font-size: 13px;
}
</style>
