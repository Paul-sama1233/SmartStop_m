<template>
  <div class="map-page">
    <div ref="mapContainer" class="fullmap"></div>

    <!-- Кнопка геолокации -->
    <button class="locate-btn" @click="locateMe" :class="{ loading: locating }">
      <span v-if="locating">⏳</span>
      <span v-else>📍</span>
    </button>

    <!-- Счётчик транспорта -->
    <div class="transport-badge">
      <span class="live-dot"></span>
      {{ vehicles.length }} в движении
    </div>

    <!-- Подсказка -->
    <div class="map-hint" v-if="hint">{{ hint }}</div>

    <!-- Переключатель слоёв -->
    <div class="map-layer-btns">
      <button :class="{ active: mapLayer === 'map' }" @click="setLayer('map')">🗺</button>
      <button :class="{ active: mapLayer === 'satellite' }" @click="setLayer('satellite')">🛰</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useTransportStore } from '../stores/transport.js'
import { storeToRefs } from 'pinia'

const store = useTransportStore()
const { vehicles } = storeToRefs(store)

const mapContainer = ref(null)
const mapLayer = ref('map')
const locating = ref(false)
const hint = ref('')

let map = null
let tileLayer = null
let userMarker = null
let accuracyCircle = null
let vehicleMarkers = []
let ws = null
let wsReconnectTimer = null

const LAYERS = {
  map: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
}

// Цвет маркера по направлению
const DIR_COLORS = { 'A-B': '#ff6b35', 'B-A': '#4a9eff' }

watch(vehicles, () => { if (map) drawVehicles() }, { deep: true })

onMounted(async () => {
  map = L.map(mapContainer.value, { zoomControl: true }).setView([41.2995, 69.2401], 12)
  tileLayer = L.tileLayer(LAYERS.map, { attribution: '© OpenStreetMap' }).addTo(map)

  // Загружаем транспорт
  await store.fetchVehicles()
  drawVehicles()

  // Реальное время через WebSocket
  connectWebSocket()

  // Запрашиваем геопозицию
  locateMe()
})

onUnmounted(() => {
  if (wsReconnectTimer) clearTimeout(wsReconnectTimer)
  if (ws) ws.close()
  if (map) map.remove()
})

function connectWebSocket() {
  ws = new WebSocket('ws://127.0.0.1:8000/ws/vehicles/')
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'vehicles_update') {
        store.vehicles = data.vehicles
        drawVehicles()
      }
    } catch (e) {}
  }
  ws.onclose = () => {
    wsReconnectTimer = setTimeout(connectWebSocket, 3000)
  }
  ws.onerror = () => { ws.close() }
}

function setLayer(type) {
  mapLayer.value = type
  if (tileLayer) map.removeLayer(tileLayer)
  tileLayer = L.tileLayer(LAYERS[type], {
    attribution: type === 'map' ? '© OpenStreetMap' : '© Esri'
  }).addTo(map)
}

// Отрисовка транспорта (только маркеры, без путей)
function drawVehicles() {
  vehicleMarkers.forEach(m => map.removeLayer(m))
  vehicleMarkers = []

  vehicles.value.forEach(v => {
    if (!v.latitude || !v.longitude) return
    const color = DIR_COLORS[v.direction] || '#00c896'
    const icon = L.divIcon({
      className: '',
      html: `<div style="
        background:${color};color:white;font-size:13px;font-weight:800;
        width:34px;height:34px;border-radius:50%;
        display:flex;align-items:center;justify-content:center;
        border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.4);
        font-family:monospace
      ">${v.route_number}</div>`,
      iconSize: [34, 34],
      iconAnchor: [17, 17],
    })
    const marker = L.marker([v.latitude, v.longitude], { icon }).addTo(map)
    marker.bindPopup(`
      <div style="font-family:sans-serif;min-width:130px">
        <div style="font-weight:700;font-size:13px">Маршрут ${v.route_number}</div>
        ${v.route_name ? `<div style="color:#888;font-size:11px">${v.route_name}</div>` : ''}
        <div style="color:${color};font-size:12px;margin-top:2px">🚌 ${Math.round(v.speed || 0)} км/ч</div>
      </div>
    `)
    vehicleMarkers.push(marker)
  })
}

function locateMe() {
  if (!navigator.geolocation) {
    hint.value = 'Геолокация не поддерживается браузером'
    return
  }
  locating.value = true
  hint.value = 'Определяем местоположение...'

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const { latitude, longitude, accuracy } = pos.coords
      showUser(latitude, longitude, accuracy)
      map.setView([latitude, longitude], 15, { animate: true })
      locating.value = false
      hint.value = ''
    },
    (err) => {
      locating.value = false
      if (err.code === 1) {
        hint.value = 'Доступ к геолокации запрещён. Разрешите в настройках браузера.'
      } else {
        hint.value = 'Не удалось определить местоположение'
      }
      setTimeout(() => { hint.value = '' }, 4000)
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
  )
}

function showUser(lat, lng, accuracy) {
  if (userMarker) map.removeLayer(userMarker)
  if (accuracyCircle) map.removeLayer(accuracyCircle)

  accuracyCircle = L.circle([lat, lng], {
    radius: accuracy || 50,
    color: '#4a9eff', fillColor: '#4a9eff', fillOpacity: 0.1, weight: 1,
  }).addTo(map)

  const icon = L.divIcon({
    className: '',
    html: `<div class="user-dot"><div class="user-pulse"></div></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  })
  userMarker = L.marker([lat, lng], { icon, zIndexOffset: 1000 }).addTo(map)
  userMarker.bindPopup('<b>Вы здесь</b>')
}
</script>

<style scoped>
.map-page { flex: 1; position: relative; overflow: hidden; }
.fullmap { position: absolute; inset: 0; width: 100%; height: 100%; }

.locate-btn {
  position: absolute; bottom: 90px; right: 16px; z-index: 1000;
  width: 48px; height: 48px; border-radius: 50%;
  background: var(--bg-card); border: 1px solid var(--border);
  box-shadow: 0 4px 16px rgba(0,0,0,0.4);
  cursor: pointer; font-size: 22px;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.locate-btn:hover { background: var(--bg-panel); border-color: var(--accent-blue); }
.locate-btn.loading { opacity: 0.7; }

.transport-badge {
  position: absolute; top: 16px; left: 16px; z-index: 1000;
  display: flex; align-items: center; gap: 8px;
  background: rgba(15,15,26,0.9); color: white;
  padding: 8px 14px; border-radius: 20px; font-size: 13px; font-weight: 700;
  border: 1px solid var(--border); backdrop-filter: blur(8px);
}
.live-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--accent-green); box-shadow: 0 0 6px var(--accent-green);
  animation: blink 2s infinite;
}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

.map-hint {
  position: absolute; top: 16px; left: 50%; transform: translateX(-50%);
  z-index: 1000; background: rgba(15,15,26,0.9); color: white;
  padding: 10px 18px; border-radius: 20px; font-size: 13px; font-weight: 600;
  border: 1px solid var(--border); backdrop-filter: blur(8px);
  max-width: 70%; text-align: center;
}

.map-layer-btns {
  position: absolute; bottom: 16px; right: 16px; z-index: 1000;
  display: flex; flex-direction: column; gap: 4px;
}
.map-layer-btns button {
  background: rgba(15,15,26,0.9); border: 1px solid var(--border);
  border-radius: 8px; width: 36px; height: 36px; cursor: pointer;
  font-size: 16px; color: white; backdrop-filter: blur(8px);
}
.map-layer-btns button.active { background: var(--accent-green); }
</style>

<style>
.user-dot { width: 20px; height: 20px; position: relative; }
.user-dot::after {
  content: ''; position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 14px; height: 14px; border-radius: 50%;
  background: #4a9eff; border: 3px solid white;
  box-shadow: 0 2px 6px rgba(0,0,0,0.4); z-index: 2;
}
.user-pulse {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 20px; height: 20px; border-radius: 50%;
  background: rgba(74,158,255,0.4);
  animation: userPulse 2s ease-out infinite;
}
@keyframes userPulse {
  0% { width: 14px; height: 14px; opacity: 0.8; }
  100% { width: 50px; height: 50px; opacity: 0; }
}
</style>
