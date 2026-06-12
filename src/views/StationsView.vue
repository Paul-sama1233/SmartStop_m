<template>
  <div class="stations-page">

    <!-- Поиск -->
    <div class="search-bar">
      <span class="search-icon">🔍</span>
      <input
        v-model="searchQuery"
        :placeholder="activeTab === 'bus' ? 'Номер маршрута...' : 'Станция метро...'"
        @input="onSearch"
      />
      <button v-if="searchQuery" class="clear-btn" @click="clearSearch">✕</button>
    </div>

    <!-- Карта -->
    <div class="map-section" :style="{ height: mapVisible ? '50vh' : '0' }">
      <div ref="mapContainer" class="map-container"></div>
      <div class="map-layer-btns" v-show="mapVisible">
        <button :class="{ active: mapLayer === 'map' }" @click="setLayer('map')">🗺</button>
        <button :class="{ active: mapLayer === 'satellite' }" @click="setLayer('satellite')">🛰</button>
      </div>
    </div>

    <!-- Кнопка карты -->
    <button class="map-toggle-btn" @click="toggleMap">
      {{ mapVisible ? '▲ Скрыть карту' : '▼ Показать карту' }}
    </button>

    <!-- Вкладки -->
    <div class="tabs">
      <button class="tab" :class="{ active: activeTab === 'bus' }" @click="switchTab('bus')">
        🚌 Автобусы
      </button>
      <button class="tab" :class="{ active: activeTab === 'metro' }" @click="switchTab('metro')">
        🚇 Метро
      </button>
    </div>

    <!-- Плитка выбранного (только для метро) -->
    <div v-if="selectedItem && activeTab === 'metro'" class="selected-card">
      <div class="selected-badge metro" :style="{ background: selectedItem.color }">М</div>
      <div class="selected-info">
        <div class="selected-line-name">{{ selectedItem.name }}</div>
        <div class="selected-endpoints">
          <span class="endpoint start">⬤ {{ selectedItem.stations?.[0]?.name }}</span>
          <span class="endpoint end">⬤ {{ selectedItem.stations?.[selectedItem.stations.length-1]?.name }}</span>
        </div>
      </div>
      <button class="close-card" @click="clearSelected">✕</button>
    </div>

    <!-- Список -->
    <div class="list-content">

      <!-- Автобусы -->
      <template v-if="activeTab === 'bus'">
        <div v-if="filteredBuses.length === 0" class="empty-state">Маршрут не найден</div>

        <div
          v-for="bus in filteredBuses"
          :key="bus.number"
          class="bus-card"
          :class="{ favorite: bus.is_favorite }"
          @click="selectBus(bus)"
        >
          <div class="bus-card-left">
            <div class="bus-number-box">
              <span class="bus-number">{{ bus.number }}</span>
            </div>
            <span v-if="bus.is_favorite" class="fav-star">⭐</span>
          </div>

          <div class="bus-card-right">
            <div class="bus-route-names">
              <span class="bus-route-a">→ {{ formatEndpoint(bus.name, 'start') }}</span>
              <span class="bus-route-b">→ {{ formatEndpoint(bus.name, 'end') }}</span>
            </div>
            <div class="bus-card-meta">
              <span class="meta-item" v-if="bus.vehicle_count > 0">
                🚌 {{ bus.vehicle_count }} авт.
              </span>
              <span class="meta-item" v-if="bus.active_vehicles > 0">
                <span class="online-dot"></span>{{ bus.active_vehicles }} в пути
              </span>
              <span class="meta-item" v-if="bus.avg_trip_minutes">
                ⏱ {{ bus.avg_trip_minutes }} мин
              </span>
              <span class="meta-item" v-if="bus.work_start">
                🕐 {{ formatTime(bus.work_start) }}–{{ formatTime(bus.work_end) }}
              </span>
            </div>
          </div>

          <div class="bus-card-arrow">›</div>
        </div>
      </template>

      <!-- Метро -->
      <template v-else>
        <div
          v-for="line in filteredMetro"
          :key="line.id"
          class="metro-row"
          :class="{ active: selectedItem?.id === line.id }"
          @click="selectMetro(line)"
        >
          <div class="metro-color-dot" :style="{ background: line.color }"></div>
          <div class="row-info">
            <span class="row-name">{{ line.name }}</span>
            <span class="row-name muted">
              {{ line.stations?.[0]?.name }} → {{ line.stations?.[line.stations.length-1]?.name }}
            </span>
          </div>
          <span class="metro-count">{{ line.stations_count }} ст.</span>
        </div>
      </template>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useTransportStore } from '../stores/transport.js'
import { storeToRefs } from 'pinia'
import api from '../api/router_index.js'

const router = useRouter()
const store = useTransportStore()
const { vehicles } = storeToRefs(store)

const mapContainer = ref(null)
const searchQuery = ref('')
const activeTab = ref('bus')
const selectedItem = ref(null)
const mapLayer = ref('map')
const mapVisible = ref(false)
const metroLines = ref([])
const busesData = ref([])

let map = null
let tileLayer = null
let vehicleMarkers = []
let metroMarkers = []
let refreshInterval = null

const LAYERS = {
  map: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
}

// Сортировка: избранные → количество транспорта → номер
const filteredBuses = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  let list = q
    ? busesData.value.filter(b => b.number.toLowerCase().includes(q))
    : [...busesData.value]

  list.sort((a, b) => {
    if (b.is_favorite !== a.is_favorite) return b.is_favorite ? 1 : -1
    if (b.vehicle_count !== a.vehicle_count) return b.vehicle_count - a.vehicle_count
    const na = parseInt(a.number)
    const nb = parseInt(b.number)
    if (!isNaN(na) && !isNaN(nb)) return na - nb
    return a.number.localeCompare(b.number)
  })

  return list
})

const filteredMetro = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return metroLines.value
  return metroLines.value.filter(line =>
    line.name.toLowerCase().includes(q) ||
    line.stations?.some(s => s.name.toLowerCase().includes(q))
  )
})

watch(mapVisible, async (val) => {
  if (val) {
    await nextTick()
    setTimeout(() => map?.invalidateSize(), 350)
  }
})

async function toggleMap() {
  mapVisible.value = !mapVisible.value
}

onMounted(async () => {
  map = L.map(mapContainer.value, { zoomControl: false })
    .setView([41.2995, 69.2401], 12)
  tileLayer = L.tileLayer(LAYERS.map, { attribution: '© OpenStreetMap' }).addTo(map)

  const [boardResp] = await Promise.all([api.getBoard(), store.fetchVehicles()])
  busesData.value = boardResp.data.buses
  metroLines.value = boardResp.data.metro

  drawVehicles()

  refreshInterval = setInterval(async () => {
    await store.fetchVehicles()
    if (mapVisible.value) drawVehicles()
  }, 10000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
  if (map) map.remove()
})

function setLayer(type) {
  mapLayer.value = type
  if (tileLayer) map.removeLayer(tileLayer)
  tileLayer = L.tileLayer(LAYERS[type], {
    attribution: type === 'map' ? '© OpenStreetMap' : '© Esri'
  }).addTo(map)
}

function drawVehicles() {
  vehicleMarkers.forEach(m => map.removeLayer(m))
  vehicleMarkers = []
  vehicles.value.forEach(v => {
    const icon = L.divIcon({
      className: '',
      html: `<div class="vehicle-marker">${v.route_number}</div>`,
      iconSize: [36, 36], iconAnchor: [18, 18],
    })
    const marker = L.marker([v.latitude, v.longitude], { icon }).addTo(map)
    marker.bindPopup(`<b>Маршрут ${v.route_number}</b><br>${v.route_name}`)
    vehicleMarkers.push(marker)
  })
}

function drawMetroOnMap() {
  clearMetroMarkers()
  metroLines.value.forEach(line => {
    const points = buildLinePoints(line)
    if (points.length > 1) {
      metroMarkers.push(
        L.polyline(points, { color: line.color, weight: 5, opacity: 0.85, smoothFactor: 1.5 }).addTo(map)
      )
    }
    line.stations?.forEach((s, i) => {
      if (!s.latitude) return
      const isTerminal = i === 0 || i === line.stations.length - 1
      const icon = L.divIcon({
        className: '',
        html: `<div style="width:${isTerminal?14:10}px;height:${isTerminal?14:10}px;border-radius:50%;background:white;border:3px solid ${line.color};box-shadow:0 1px 4px rgba(0,0,0,0.4)"></div>`,
        iconSize: [isTerminal?14:10, isTerminal?14:10],
        iconAnchor: [isTerminal?7:5, isTerminal?7:5],
      })
      const m = L.marker([s.latitude, s.longitude], { icon }).addTo(map)
      m.bindPopup(`<b>${s.name}</b><br>${line.name}`)
      metroMarkers.push(m)
    })
  })
}

function buildLinePoints(line) {
  const stations = line.stations || []
  const waypoints = line.waypoints || []
  const points = []
  stations.forEach((station, i) => {
    if (!station.latitude) return
    points.push([station.latitude, station.longitude])
    if (i < stations.length - 1) {
      waypoints.filter(wp => wp.after_station === i).forEach(wp => {
        points.push([wp.lat, wp.lng])
      })
    }
  })
  return points
}

function clearMetroMarkers() {
  metroMarkers.forEach(m => map.removeLayer(m))
  metroMarkers = []
}

function clearVehicleMarkers() {
  vehicleMarkers.forEach(m => map?.removeLayer(m))
  vehicleMarkers = []
}

// При выборе автобуса — переходим на страницу маршрута
function selectBus(bus) {
  router.push(`/route/${bus.number}`)
}

function selectMetro(line) {
  selectedItem.value = line
  mapVisible.value = true
  nextTick(() => {
    setTimeout(() => {
      map?.invalidateSize()
      clearMetroMarkers()
      const coords = []
      const points = buildLinePoints(line)
      if (points.length > 1) {
        metroMarkers.push(
          L.polyline(points, { color: line.color, weight: 6, opacity: 0.9, smoothFactor: 2 }).addTo(map)
        )
      }
      line.stations?.forEach((s, i) => {
        if (!s.latitude) return
        coords.push([s.latitude, s.longitude])
        const isTerminal = i === 0 || i === line.stations.length - 1
        const icon = L.divIcon({
          className: '',
          html: `<div style="width:${isTerminal?16:12}px;height:${isTerminal?16:12}px;border-radius:50%;background:${isTerminal?line.color:'white'};border:3px solid ${line.color};box-shadow:0 2px 6px rgba(0,0,0,0.4)"></div>`,
          iconSize: [isTerminal?16:12, isTerminal?16:12],
          iconAnchor: [isTerminal?8:6, isTerminal?8:6],
        })
        const m = L.marker([s.latitude, s.longitude], { icon }).addTo(map)
        m.bindPopup(`<b>${s.name}</b><br>${line.name}`)
        metroMarkers.push(m)
      })
      if (coords.length > 0) {
        try { map.fitBounds(L.latLngBounds(coords), { padding: [40, 40] }) } catch (e) {}
      }
    }, 350)
  })
}

function switchTab(tab) {
  activeTab.value = tab
  selectedItem.value = null
  searchQuery.value = ''
  clearMetroMarkers()
  clearVehicleMarkers()
  if (tab === 'metro' && mapVisible.value) drawMetroOnMap()
  else if (tab === 'bus' && mapVisible.value) drawVehicles()
}

// Поиск — только фильтрует список, НЕ переходит на маршрут
function onSearch() {
  selectedItem.value = null
  clearMetroMarkers()
  clearVehicleMarkers()
}

function clearSearch() {
  searchQuery.value = ''
  selectedItem.value = null
  clearMetroMarkers()
  if (activeTab.value === 'metro' && mapVisible.value) drawMetroOnMap()
  else if (mapVisible.value) drawVehicles()
}

function clearSelected() {
  selectedItem.value = null
  clearMetroMarkers()
  if (mapVisible.value) drawVehicles()
}

function formatEndpoint(name, part) {
  if (!name) return ''
  const parts = name.split('-')
  if (parts.length < 2) return name
  return part === 'start' ? parts[0].trim() : parts[parts.length - 1].trim()
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  return timeStr.substring(0, 5)
}
</script>

<style scoped>
.stations-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  background: var(--bg-dark);
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 18px 20px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.search-icon { font-size: 25px; }
.search-bar input {
  flex: 1; background: none; border: none; outline: none;
  color: var(--text-primary); font-size: 20px; font-family: var(--font-main);
}
.search-bar input::placeholder { color: var(--text-secondary); }
.clear-btn { background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 20px; }

.map-section {
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
  transition: height 0.35s cubic-bezier(0.4,0,0.2,1);
}
.map-container { width: 100%; height: 100%; }

.map-layer-btns {
  position: absolute; bottom: 10px; right: 10px; z-index: 1000;
  display: flex; flex-direction: column; gap: 4px;
}
.map-layer-btns button {
  background: rgba(15,15,26,0.9); border: 1px solid var(--border);
  border-radius: 8px; width: 36px; height: 36px; cursor: pointer;
  font-size: 16px; color: white; backdrop-filter: blur(8px);
}
.map-layer-btns button.active { background: var(--accent-green); }

.map-toggle-btn {
  width: 100%; padding: 7px;
  background: var(--bg-panel);
  border: none; border-bottom: 1px solid var(--border);
  color: var(--text-secondary); font-size: 15px; font-weight: 600;
  cursor: pointer; font-family: var(--font-main); flex-shrink: 0;
  transition: all 0.15s;
}
.map-toggle-btn:hover { color: var(--accent-green); }

.tabs {
  display: flex; background: var(--bg-card);
  border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.tab {
  flex: 1; padding: 12px; background: none; border: none;
  border-bottom: 2px solid transparent; color: var(--text-secondary);
  font-size: 20px; font-weight: 700; cursor: pointer;
  font-family: var(--font-main); transition: all 0.2s;
}
.tab.active { color: var(--accent-green); border-bottom-color: var(--accent-green); }

.selected-card {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px;
  background: rgba(0,200,150,0.08);
  border-bottom: 1px solid rgba(0,200,150,0.2); flex-shrink: 0;
}
.selected-badge {
  width: 44px; height: 44px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; font-weight: 800; font-family: var(--font-mono); flex-shrink: 0;
}
.selected-badge.metro { color: white; }
.selected-info { flex: 1; display: flex; flex-direction: column; gap: 3px; overflow: hidden; }
.selected-line-name { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.selected-endpoints { display: flex; flex-direction: column; gap: 1px; }
.endpoint { font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.endpoint.start { color: var(--accent-green); }
.endpoint.end { color: var(--accent-orange); }
.close-card { background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 18px; flex-shrink: 0; }

.list-content { flex: 1; overflow-y: auto; }
.empty-state { text-align: center; padding: 40px 16px; color: var(--text-secondary); font-size: 15px; }

/* Карточка автобуса */
.bus-card {
  display: flex;
  align-items: stretch;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.15s;
  overflow: hidden;
}
.bus-card:hover { background: rgba(0,200,150,0.06); }
.bus-card.favorite { border-left: 3px solid var(--accent-green); }

.bus-card-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 17px 13px;
  gap: 4px;
  min-width: 68px;
  background: rgba(255,255,255,0.02);
  border-right: 1px solid var(--border);
  flex-shrink: 0;
}
.bus-number-box {
  width: 48px; height: 48px;
  background: var(--bg-panel);
  border-radius: 10px;
  border: 1px solid var(--border);
  display: flex; align-items: center; justify-content: center;
}
.bus-number {
  font-size: 20px; font-weight: 800;
  color: var(--accent-green);
  font-family: var(--font-mono);
}
.fav-star { font-size: 12px; }

.bus-card-right {
  flex: 1;
  padding: 14px 16px;
  display: flex; flex-direction: column; gap: 6px;
  overflow: hidden;
}
.bus-route-names { display: flex; flex-direction: column; gap: 3px; }
.bus-route-a {
  font-size: 16px; font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.bus-route-b {
  font-size: 16px; color: var(--text-secondary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.bus-card-meta {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}
.meta-item {
  font-size: 15px; color: var(--text-secondary);
  display: flex; align-items: center; gap: 4px;
}
.online-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--accent-green);
  box-shadow: 0 0 5px var(--accent-green);
  display: inline-block;
}
.bus-card-arrow {
  display: flex; align-items: center;
  padding: 0 14px;
  color: var(--text-secondary);
  font-size: 24px;
  flex-shrink: 0;
}

/* Метро */
.metro-row {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; border-bottom: 1px solid var(--border);
  cursor: pointer; transition: background 0.15s;
}
.metro-row:hover, .metro-row.active { background: rgba(255,255,255,0.04); }
.metro-color-dot { width: 16px; height: 16px; border-radius: 50%; flex-shrink: 0; }
.row-info { flex: 1; display: flex; flex-direction: column; gap: 3px; overflow: hidden; }
.row-name {
  font-size: 15px; font-weight: 600; color: var(--text-primary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.row-name.muted { color: var(--text-secondary); font-weight: 400; font-size: 13px; }
.metro-count { font-size: 12px; color: var(--text-secondary); flex-shrink: 0; }
</style>
