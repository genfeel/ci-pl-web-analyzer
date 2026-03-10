<template>
  <div
    class="upload-area"
    :class="{ dragging }"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
    @drop.prevent="onDrop"
  >
    <div class="upload-content">
      <div class="upload-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#667" stroke-width="1.5">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
      </div>
      <p class="upload-text">CI Excel 파일을 드래그하거나 클릭하여 업로드</p>
      <p class="upload-hint">.xls, .xlsx 파일 지원</p>
      <input
        ref="fileInput"
        type="file"
        accept=".xls,.xlsx"
        style="display:none"
        @change="onFileSelect"
      />
      <button class="upload-btn" @click="$refs.fileInput.click()">파일 선택</button>
    </div>
    <div v-if="store.loading" class="loading-overlay">
      <div class="spinner"></div>
      <p>분석 중...</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { usePackingStore } from '../stores/packingStore.js'

const store = usePackingStore()
const dragging = ref(false)

function onDrop(e) {
  dragging.value = false
  const file = e.dataTransfer.files[0]
  if (file) handleFile(file)
}

function onFileSelect(e) {
  const file = e.target.files[0]
  if (file) handleFile(file)
}

function handleFile(file) {
  const ext = file.name.split('.').pop().toLowerCase()
  if (!['xls', 'xlsx'].includes(ext)) {
    store.error = 'xls 또는 xlsx 파일만 업로드 가능합니다.'
    return
  }
  store.upload(file)
}
</script>

<style scoped>
.upload-area {
  position: relative;
  border: 2px dashed #ccc;
  border-radius: 12px;
  padding: 48px 24px;
  text-align: center;
  transition: all 0.2s;
  background: #fff;
  cursor: pointer;
}
.upload-area.dragging {
  border-color: #2196F3;
  background: #e3f2fd;
}
.upload-icon { margin-bottom: 16px; }
.upload-text { font-size: 16px; color: #555; margin-bottom: 8px; }
.upload-hint { font-size: 13px; color: #999; margin-bottom: 20px; }
.upload-btn {
  padding: 10px 28px;
  background: #2196F3;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}
.upload-btn:hover { background: #1976D2; }
.loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255,255,255,0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  gap: 12px;
}
.loading-overlay p { color: #555; font-size: 14px; }
.spinner {
  width: 36px; height: 36px;
  border: 3px solid #e0e0e0;
  border-top-color: #2196F3;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
