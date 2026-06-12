import { defineStore } from 'pinia'
import api from '../api/index.js'

export const useTransportStore = defineStore('transport', {
  state: () => ({
    routes: [],
    vehicles: [],
    metroLines: [],
    boardData: null,
    loading: false,
    error: null,
  }),

  actions: {
    async fetchRoutes() {
      this.loading = true
      try {
        const response = await api.getRoutes()
        this.routes = response.data
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },

    async fetchVehicles() {
      try {
        const response = await api.getVehiclesOnMap()
        this.vehicles = response.data
      } catch (e) {
        this.error = e.message
      }
    },

    async fetchMetroLines() {
      try {
        const response = await api.getMetroLines()
        this.metroLines = response.data
      } catch (e) {
        this.error = e.message
      }
    },

    async fetchBoard() {
      this.loading = true
      try {
        const response = await api.getBoard()
        this.boardData = response.data
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
  }
})
