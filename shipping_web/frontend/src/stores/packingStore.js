import { defineStore } from 'pinia'
import { uploadFile, downloadPL, loadContainer } from '../api/client.js'

export const usePackingStore = defineStore('packing', {
  state: () => ({
    packingResult: null,
    containerResult: null,
    loading: false,
    error: null,
    selectedContainerType: '40ft',
  }),

  getters: {
    resultId: (state) => state.packingResult?.result_id,
    cases: (state) => state.packingResult?.cases || [],
    validation: (state) => state.packingResult?.validation,
    categorySummary: (state) => state.packingResult?.category_summary || [],
  },

  actions: {
    async upload(file) {
      this.loading = true
      this.error = null
      this.packingResult = null
      this.containerResult = null
      try {
        this.packingResult = await uploadFile(file)
      } catch (e) {
        this.error = e.response?.data?.detail || e.message
      } finally {
        this.loading = false
      }
    },

    async downloadPL() {
      if (!this.resultId) return
      try {
        await downloadPL(this.resultId)
      } catch (e) {
        this.error = e.response?.data?.detail || e.message
      }
    },

    async simulateContainer(type) {
      if (!this.resultId) return
      this.selectedContainerType = type
      this.loading = true
      this.error = null
      try {
        this.containerResult = await loadContainer(this.resultId, type)
      } catch (e) {
        this.error = e.response?.data?.detail || e.message
      } finally {
        this.loading = false
      }
    },

    reset() {
      this.packingResult = null
      this.containerResult = null
      this.loading = false
      this.error = null
    },
  },
})
