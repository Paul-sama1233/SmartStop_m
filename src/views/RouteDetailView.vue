<template>
  <div class="route-detail-page">

    <!-- Шапка -->
    <div class="detail-header">
      <button class="back-btn" @click="$router.back()">←</button>
      <div class="header-info">
        <div class="header-number">Маршрут {{ routeNumber }}</div>
        <div class="header-sub" v-if="currentRoute">
          {{ formatName(currentRoute.name, currentDir) }}
        </div>
      </div>
      <button class="dir-toggle-btn" @click="toggleDir" title="Сменить направление">⇄</button>
    </div>

    <!-- Карта -->
    <div class="map-section">
      <div ref="mapContainer" class="map-container"></div>
      <div class="map-legend">
        <div class="legend-item" :class="{ active: currentDir === 'A-B' }" @click="setDirection('A-B')">
          <div class="legend-line ab"></div>
          <span>→ Прямое</span>
        </div>
        <div class="legend-item" :class="{ active: currentDir === 'B-A' }" @click="setDirection('B-A')">
          <div class="legend-line ba"></div>
          <span>← Обратное</span>
        </div>
      </div>
      <div class="map-layer-btns">
        <button :class="{ active: mapLayer === 'map' }" @click="setLayer('map')">🗺</button>
        <button :class="{ active: mapLayer === 'satellite' }" @click="setLayer('satellite')">🛰</button>
      </div>
    </div>

    <!-- Переключатель направлений -->
    <div class="direction-tabs">
      <button class="dir-btn ab" :class="{ active: currentDir === 'A-B' }" @click="setDirection('A-B')">→ Прямое</button>
      <button class="dir-btn ba" :class="{ active: currentDir === 'B-A' }" @click="setDirection('B-A')">← Обратное</button>
    </div>

    <!-- Мета -->
    <div class="route-meta" v-if="currentRoute">
      <span class="meta-chip" v-if="currentRoute.vehicle_count > 0">🚌 {{ currentRoute.vehicle_count }} авт.</span>
      <span class="meta-chip" v-if="currentRoute.avg_trip_minutes">⏱ {{ currentRoute.avg_trip_minutes }} мин</span>
      <span class="meta-chip" v-if="currentRoute.work_start">🕐 {{ formatTime(currentRoute.work_start) }}–{{ formatTime(currentRoute.work_end) }}</span>
      <span class="meta-chip live-chip" v-if="activeVehicles.length > 0">
        <span class="live-dot"></span>{{ activeVehicles.length }} в пути
      </span>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Загружаем данные...</span>
    </div>

    <!-- Список остановок -->
    <div v-else-if="currentStops.length > 0" class="stops-container">
      <div class="dir-label">
        <div class="dir-badge" :class="currentDir === 'A-B' ? 'ab' : 'ba'">
          {{ currentDir === 'A-B' ? '→' : '←' }}
        </div>
        <span>
          {{ currentDir === 'A-B'
            ? formatEndpoint(currentRoute?.name, 'start') + ' → ' + formatEndpoint(currentRoute?.name, 'end')
            : formatEndpoint(currentRoute?.name, 'end') + ' → ' + formatEndpoint(currentRoute?.name, 'start')
          }}
        </span>
        <span class="stops-total">{{ currentStops.length }} ост.</span>
      </div>

      <div class="stops-list">
        <div
          v-for="(routeStop, index) in currentStops"
          :key="routeStop.order"
          class="stop-row"
          :class="{ expanded: selectedStop?.order === routeStop.order }"
          @click="selectStop(routeStop)"
        >
          <!-- Левая колонка -->
          <div class="stop-left">
            <div
              class="stop-dot"
              :class="{
                terminal: index === 0 || index === currentStops.length - 1,
                'has-vehicle': hasVehicleAt(routeStop),
                selected: selectedStop?.order === routeStop.order
              }"
            ></div>
            <div
              class="stop-line"
              v-if="index < currentStops.length - 1"
              :class="currentDir === 'A-B' ? 'orange' : 'blue'"
            ></div>
          </div>

          <!-- Центр -->
          <div class="stop-center">
            <div class="stop-top">
              <span
                class="stop-name"
                :class="{ terminal: index === 0 || index === currentStops.length - 1 }"
              >{{ routeStop.stop.name }}</span>
              <span class="stop-num">{{ routeStop.order }}</span>
            </div>
            <div class="vehicle-row" v-if="hasVehicleAt(routeStop)">
              <span class="vehicle-pill">🚌 {{ getVehicleAt(routeStop)?.speed?.toFixed(0) }} км/ч</span>
            </div>
            <div class="stop-dist"
              v-if="index < currentStops.length - 1 && calcDist(routeStop, currentStops[index+1])">
              {{ calcDist(routeStop, currentStops[index+1]) }} м
            </div>

            <!-- Панель маршрутов через остановку (раскрывается) -->
            <div v-if="selectedStop?.order === routeStop.order" class="stop-routes-panel">
              <div v-if="loadingRoutes" class="routes-loading">Загружаем...</div>
              <template v-else>
                <div class="routes-panel-label">Маршруты через эту остановку:</div>
                <div class="routes-panel-chips">
                  <span
                    v-for="num in stopRoutes"
                    :key="num"
                    class="route-chip"
                    :class="{ current: String(num) === String(routeNumber) }"
                    @click.stop="goToRoute(num)"
                  >🚌 {{ num }}</span>
                </div>
                <div v-if="stopRoutes.length === 0" class="routes-empty">Нет данных</div>
              </template>
            </div>
          </div>

          <!-- ETA -->
          <div class="stop-right">
            <template v-if="nearestVehicleInfo">
              <span class="eta-bus" v-if="calcDynamicETA(index) === null">🚌</span>
              <span class="eta-now" v-else-if="calcDynamicETA(index) === 0">~1 мин</span>
              <span class="eta-min" v-else>
                {{ calcDynamicETA(index) }}<span class="eta-unit">мин</span>
              </span>
            </template>
            <template v-else>
              <span class="eta-val" v-if="index === 0">Старт</span>
              <span class="eta-min" v-else-if="routeStop.estimated_time > 0">
                {{ routeStop.estimated_time }}<span class="eta-unit">мин</span>
              </span>
            </template>
            <span class="eta-km" v-if="routeStop.distance_from_start > 0">
              {{ routeStop.distance_from_start }} км
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">Остановки не найдены</div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTransportStore } from '../stores/transport.js'
import { storeToRefs } from 'pinia'
import api from '../api/index.js'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const route = useRoute()
const router = useRouter()
const store = useTransportStore()
const { vehicles } = storeToRefs(store)

const routeNumber = route.params.number
const loading = ref(true)
const currentDir = ref('A-B')
const allRoutes = ref([])
const mapContainer = ref(null)
const mapLayer = ref('map')

// Выбранная остановка и маршруты через неё
const selectedStop = ref(null)
const stopRoutes = ref([])
const loadingRoutes = ref(false)

let map = null
let tileLayer = null
let routeLines = { 'A-B': null, 'B-A': null }
let stopMarkers = []
let vehicleMarkers = []
let ws = null
let wsReconnectTimer = null

const LAYERS = {
  map: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
}

const DIR_COLORS = { 'A-B': '#ff6b35', 'B-A': '#4a9eff' }

const currentRoute = computed(() =>
  allRoutes.value.find(r => r.direction === (currentDir.value === 'A-B' ? 'B-A' : 'A-B'))
)
const currentStops = computed(() => currentRoute.value?.stops || [])
const activeVehicles = computed(() =>
  vehicles.value.filter(v => {
    if (String(v.route_number) !== String(routeNumber)) return false
    const dataDir = currentDir.value === 'A-B' ? 'B-A' : 'A-B'
    if (v.direction) return v.direction === dataDir
    return true
  })
)

const nearestVehicleInfo = computed(() => {
  if (activeVehicles.value.length === 0 || currentStops.value.length === 0) return null
  const vehicle = activeVehicles.value[0]
  if (!vehicle?.latitude) return null

  let nearestIdx = 0
  let minDist = Infinity
  currentStops.value.forEach((rs, i) => {
    if (!rs.stop?.latitude) return
    const d = haversineM(vehicle.latitude, vehicle.longitude, rs.stop.latitude, rs.stop.longitude)
    if (d < minDist) { minDist = d; nearestIdx = i }
  })

  const nearestStop = currentStops.value[nearestIdx]?.stop
  const distToNearest = nearestStop?.latitude
    ? haversineM(vehicle.latitude, vehicle.longitude, nearestStop.latitude, nearestStop.longitude)
    : 0

  return { vehicle, nearestIdx, distToNearest, speed: Math.max(vehicle.speed || 25, 10) }
})

function calcDynamicETA(stopIndex) {
  const info = nearestVehicleInfo.value
  if (!info) return currentStops.value[stopIndex]?.estimated_time || null

  const { nearestIdx, distToNearest, speed } = info
  const speedMs = speed / 3.6

  if (stopIndex < nearestIdx) return null
  if (stopIndex === nearestIdx) {
    const secs = distToNearest / speedMs
    return secs < 60 ? 0 : Math.round(secs / 60)
  }

  let totalDist = distToNearest
  for (let i = nearestIdx; i < stopIndex; i++) {
    const s1 = currentStops.value[i]?.stop
    const s2 = currentStops.value[i + 1]?.stop
    if (!s1?.latitude || !s2?.latitude) continue
    totalDist += haversineM(s1.latitude, s1.longitude, s2.latitude, s2.longitude)
  }
  return Math.round((totalDist / speedMs) / 60)
}

function haversineM(lat1, lng1, lat2, lng2) {
  const R = 6371000
  const dlat = (lat2 - lat1) * Math.PI / 180
  const dlng = (lng2 - lng1) * Math.PI / 180
  const a = Math.sin(dlat/2)**2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dlng/2)**2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
}

// Выбор остановки — раскрывает панель маршрутов
async function selectStop(routeStop) {
  // Повторный клик — закрывает панель
  if (selectedStop.value?.order === routeStop.order) {
    selectedStop.value = null
    stopRoutes.value = []
    return
  }

  selectedStop.value = routeStop
  stopRoutes.value = []
  focusStop(routeStop)

  // Загружаем ближайшие маршруты через эту остановку
  if (routeStop.stop?.latitude) {
    loadingRoutes.value = true
    try {
      const resp = await api.getNearbyStops(
        routeStop.stop.latitude,
        routeStop.stop.longitude,
        30  // радиус 30м — ищем именно эту остановку
      )
      // Берём маршруты из ближайшей остановки (самой близкой)
      const nearest = resp.data.stops?.[0]
      stopRoutes.value = nearest?.routes || []
    } catch (e) {
      console.error(e)
      stopRoutes.value = []
    } finally {
      loadingRoutes.value = false
    }
  }
}

function goToRoute(num) {
  if (String(num) === String(routeNumber)) return
  router.push(`/route/${num}`)
}

watch(currentDir, () => {
  if (map) { updateRouteStyles(); drawStopMarkers(); drawVehicleMarkers() }
  selectedStop.value = null
  stopRoutes.value = []
})
watch(vehicles, () => { if (map) drawVehicleMarkers() }, { deep: true })

onMounted(async () => {
  map = L.map(mapContainer.value, { zoomControl: false }).setView([41.2995, 69.2401], 12)
  tileLayer = L.tileLayer(LAYERS.map, { attribution: '© OpenStreetMap' }).addTo(map)

  try {
    const resp = await api.getRouteByNumber(routeNumber)
    allRoutes.value = resp.data
    const hasBA = allRoutes.value.some(r => r.direction === 'B-A')
    currentDir.value = hasBA ? 'B-A' : (allRoutes.value[0]?.direction || 'B-A')
    drawBothRoutes()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }

  connectWebSocket()
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
      if (data.type === 'vehicles_update') { store.vehicles = data.vehicles; drawVehicleMarkers() }
    } catch (e) {}
  }
  ws.onclose = () => { wsReconnectTimer = setTimeout(connectWebSocket, 3000) }
  ws.onerror = () => { ws.close() }
}

function setLayer(type) {
  mapLayer.value = type
  if (tileLayer) map.removeLayer(tileLayer)
  tileLayer = L.tileLayer(LAYERS[type], { attribution: type === 'map' ? '© OpenStreetMap' : '© Esri' }).addTo(map)
}

function drawBothRoutes() {
  Object.values(routeLines).forEach(l => { if (l) map.removeLayer(l) })
  routeLines = { 'A-B': null, 'B-A': null }
  const bounds = []

  allRoutes.value.forEach(r => {
    const visualDir = r.direction === 'A-B' ? 'B-A' : 'A-B'
    const color = DIR_COLORS[visualDir]
    const isActive = visualDir === currentDir.value
    const coords = r.coordinates.map(c => [c[1], c[0]])
    const line = L.polyline(coords, {
      color, weight: isActive ? 5 : 3, opacity: isActive ? 0.95 : 0.5, dashArray: isActive ? null : '8 4',
    }).addTo(map)
    line.on('click', () => { setDirection(visualDir) })
    line.bindTooltip(`<b>${visualDir === 'A-B' ? '→ Прямое' : '← Обратное'}</b><br>Нажмите для выбора`, { sticky: true })
    routeLines[visualDir] = line
    coords.forEach(c => bounds.push(c))
  })

  if (bounds.length > 0) {
    try { map.fitBounds(L.latLngBounds(bounds), { padding: [20, 20] }) } catch (e) {}
  }
  drawStopMarkers()
  drawVehicleMarkers()
}

function updateRouteStyles() {
  Object.entries(routeLines).forEach(([dir, line]) => {
    if (!line) return
    const isActive = dir === currentDir.value
    line.setStyle({ weight: isActive ? 5 : 3, opacity: isActive ? 0.95 : 0.5, dashArray: isActive ? null : '8 4' })
    if (isActive) line.bringToFront()
  })
  drawStopMarkers()
}

function drawStopMarkers() {
  stopMarkers.forEach(m => map.removeLayer(m))
  stopMarkers = []
  currentStops.value.forEach((routeStop, i) => {
    const stop = routeStop.stop
    if (!stop?.latitude) return
    const isTerminal = i === 0 || i === currentStops.value.length - 1
    const color = DIR_COLORS[currentDir.value]
    const icon = L.divIcon({
      className: '',
      html: `<div style="width:${isTerminal?14:9}px;height:${isTerminal?14:9}px;border-radius:50%;background:${isTerminal?color:'white'};border:2px solid ${color};box-shadow:0 1px 4px rgba(0,0,0,0.4)"></div>`,
      iconSize: [isTerminal?14:9, isTerminal?14:9],
      iconAnchor: [isTerminal?7:4, isTerminal?7:4],
    })
    const marker = L.marker([stop.latitude, stop.longitude], { icon }).addTo(map)
    marker.bindPopup(`
      <div style="font-family:sans-serif;min-width:140px">
        <div style="font-weight:700;font-size:13px">${stop.name}</div>
        <div style="color:#888;font-size:11px">Остановка ${routeStop.order}</div>
        ${routeStop.estimated_time > 0 ? `<div style="color:${color};font-size:11px">⏱ ~${routeStop.estimated_time} мин</div>` : ''}
      </div>
    `)
    stopMarkers.push(marker)
  })
}

function drawVehicleMarkers() {
  vehicleMarkers.forEach(m => map.removeLayer(m))
  vehicleMarkers = []
  const filtered = vehicles.value.filter(v => {
    if (String(v.route_number) !== String(routeNumber)) return false
    const dataDir = currentDir.value === 'A-B' ? 'B-A' : 'A-B'
    if (v.direction) return v.direction === dataDir
    return true
  })
  filtered.forEach(v => {
    const color = DIR_COLORS[v.direction] || '#00c896'
    const icon = L.divIcon({
      className: '',
      html: `<div style="background:${color};color:white;font-size:13px;font-weight:800;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.4);font-family:monospace">${v.route_number}</div>`,
      iconSize: [36, 36], iconAnchor: [18, 18],
    })
    const marker = L.marker([v.latitude, v.longitude], { icon }).addTo(map)
    marker.bindPopup(`
      <div style="font-family:sans-serif;min-width:130px">
        <div style="font-weight:700;font-size:13px">Маршрут ${v.route_number}</div>
        <div style="color:${color};font-size:12px">${v.direction === 'A-B' ? '→ Прямое' : '← Обратное'}</div>
        <div style="color:#888;font-size:12px">🚌 ${Math.round(v.speed || 0)} км/ч</div>
      </div>
    `)
    vehicleMarkers.push(marker)
  })
}

function focusStop(routeStop) {
  if (!routeStop.stop?.latitude || !map) return
  map.setView([routeStop.stop.latitude, routeStop.stop.longitude], 16, { animate: true, duration: 0.5 })
  stopMarkers.forEach(m => {
    const pos = m.getLatLng()
    if (Math.abs(pos.lat - routeStop.stop.latitude) < 0.0001 &&
        Math.abs(pos.lng - routeStop.stop.longitude) < 0.0001) {
      m.openPopup()
    }
  })
}

function setDirection(dir) { if (currentDir.value !== dir) currentDir.value = dir }
function toggleDir() { currentDir.value = currentDir.value === 'A-B' ? 'B-A' : 'A-B' }

function formatEndpoint(name, part) {
  if (!name) return ''
  const parts = name.split('-')
  if (parts.length < 2) return name
  return part === 'start' ? parts[0].trim() : parts[parts.length - 1].trim()
}
function formatName(name, dir) {
  if (!name) return ''
  const parts = name.split('-')
  if (parts.length < 2) return name
  return dir === 'A-B'
    ? `${parts[0].trim()} → ${parts[parts.length-1].trim()}`
    : `${parts[parts.length-1].trim()} → ${parts[0].trim()}`
}
function formatTime(t) { return t ? t.substring(0, 5) : '' }

function hasVehicleAt(routeStop) {
  if (!routeStop.stop?.latitude) return false
  return activeVehicles.value.some(v =>
    Math.abs(v.latitude - routeStop.stop.latitude) < 0.003 &&
    Math.abs(v.longitude - routeStop.stop.longitude) < 0.003
  )
}
function getVehicleAt(routeStop) {
  if (!routeStop.stop?.latitude) return null
  return activeVehicles.value.find(v =>
    Math.abs(v.latitude - routeStop.stop.latitude) < 0.003 &&
    Math.abs(v.longitude - routeStop.stop.longitude) < 0.003
  )
}
function calcDist(s1, s2) {
  if (!s1.stop?.latitude || !s2.stop?.latitude) return null
  const d = Math.round(haversineM(s1.stop.latitude, s1.stop.longitude, s2.stop.latitude, s2.stop.longitude))
  return d > 50 ? d : null
}
</script>

<style scoped>
.route-detail-page { display: flex; flex-direction: column; flex: 1; overflow: hidden; background: var(--bg-dark); }

.detail-header {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; background: var(--bg-card);
  border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.back-btn {
  background: none; border: none; color: var(--accent-green);
  font-size: 24px; cursor: pointer; width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 8px; transition: background 0.15s; flex-shrink: 0;
}
.back-btn:hover { background: rgba(0,200,150,0.1); }
.header-info { flex: 1; display: flex; flex-direction: column; gap: 2px; overflow: hidden; }
.header-number { font-size: 18px; font-weight: 800; color: var(--accent-green); font-family: var(--font-mono); }
.header-sub { font-size: 12px; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dir-toggle-btn {
  background: var(--bg-panel); border: 1px solid var(--border);
  border-radius: 8px; color: var(--text-primary); font-size: 18px;
  width: 36px; height: 36px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: all 0.15s;
}
.dir-toggle-btn:hover { border-color: var(--accent-green); color: var(--accent-green); }

.map-section { height: 33vh; flex-shrink: 0; position: relative; }
.map-container { width: 100%; height: 100%; }

.map-legend {
  position: absolute; bottom: 10px; left: 10px; z-index: 1000;
  display: flex; flex-direction: column; gap: 5px;
}
.legend-item {
  display: flex; align-items: center; gap: 6px; padding: 5px 10px;
  border-radius: 16px; background: rgba(15,15,26,0.85); cursor: pointer;
  border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(8px);
  font-size: 11px; font-weight: 700; color: var(--text-secondary); transition: all 0.2s;
}
.legend-item.active:first-child { border-color: #ff6b35; color: #ff6b35; }
.legend-item.active:last-child { border-color: #4a9eff; color: #4a9eff; }
.legend-line { width: 24px; height: 3px; border-radius: 2px; }
.legend-line.ab { background: #ff6b35; }
.legend-line.ba { background: #4a9eff; }

.map-layer-btns {
  position: absolute; bottom: 10px; right: 10px; z-index: 1000;
  display: flex; flex-direction: column; gap: 4px;
}
.map-layer-btns button {
  background: rgba(15,15,26,0.9); border: 1px solid var(--border);
  border-radius: 8px; width: 32px; height: 32px; cursor: pointer;
  font-size: 14px; color: white; backdrop-filter: blur(8px);
}
.map-layer-btns button.active { background: var(--accent-green); }

.direction-tabs {
  display: flex; gap: 8px; padding: 10px 16px;
  background: var(--bg-card); border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.dir-btn {
  flex: 1; padding: 9px; border-radius: 10px;
  border: 1px solid var(--border); background: transparent;
  color: var(--text-secondary); font-size: 14px; font-weight: 700;
  cursor: pointer; font-family: var(--font-main); transition: all 0.2s;
}
.dir-btn.ab.active { background: #ff6b35; border-color: #ff6b35; color: #000; }
.dir-btn.ba.active { background: #4a9eff; border-color: #4a9eff; color: #000; }
.dir-btn:not(.active):hover { border-color: var(--text-secondary); }

.route-meta {
  display: flex; gap: 8px; padding: 10px 16px; flex-wrap: wrap;
  border-bottom: 1px solid var(--border); flex-shrink: 0; background: var(--bg-card);
}
.meta-chip {
  padding: 4px 10px; border-radius: 20px; background: var(--bg-panel);
  border: 1px solid var(--border); font-size: 13px; color: var(--text-secondary);
  display: flex; align-items: center; gap: 4px;
}
.live-chip { border-color: var(--accent-green); color: var(--accent-green); }
.live-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--accent-green); box-shadow: 0 0 5px var(--accent-green);
  animation: blink 2s infinite;
}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

.loading-state {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 16px; color: var(--text-secondary); font-size: 14px;
}
.spinner {
  width: 32px; height: 32px; border: 3px solid var(--border);
  border-top-color: var(--accent-green); border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.stops-container { flex: 1; overflow: hidden; display: flex; flex-direction: column; }

.dir-label {
  display: flex; align-items: center; gap: 8px; padding: 10px 16px;
  font-size: 13px; color: var(--text-secondary);
  border-bottom: 1px solid var(--border); flex-shrink: 0; background: var(--bg-panel);
}
.dir-badge {
  width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 700; flex-shrink: 0;
}
.dir-badge.ab { background: rgba(255,107,53,0.2); color: #ff6b35; }
.dir-badge.ba { background: rgba(74,158,255,0.2); color: #4a9eff; }
.stops-total {
  margin-left: auto; font-size: 12px; color: var(--text-secondary);
  background: var(--bg-card); padding: 2px 8px;
  border-radius: 10px; border: 1px solid var(--border);
}

.stops-list { flex: 1; overflow-y: auto; padding: 0 16px; }

.stop-row {
  display: flex; align-items: flex-start;
  gap: 12px; min-height: 54px; cursor: pointer;
  border-radius: 4px; transition: background 0.1s;
}
.stop-row:hover { background: rgba(255,255,255,0.03); }
.stop-row.expanded { background: rgba(0,200,150,0.05); border-radius: 8px; }

.stop-left {
  display: flex; flex-direction: column; align-items: center;
  width: 18px; flex-shrink: 0; padding-top: 16px;
}
.stop-dot {
  width: 12px; height: 12px; border-radius: 50%;
  border: 2px solid var(--text-secondary);
  background: var(--bg-dark); flex-shrink: 0; z-index: 1; transition: all 0.2s;
}
.stop-dot.terminal { width: 14px; height: 14px; border-color: var(--accent-green); background: var(--accent-green); }
.stop-dot.has-vehicle { border-color: #ff6b35 !important; background: #ff6b35 !important; box-shadow: 0 0 8px rgba(255,107,53,0.6); width: 14px; height: 14px; }
.stop-dot.selected { border-color: var(--accent-green) !important; box-shadow: 0 0 8px rgba(0,200,150,0.6); width: 14px; height: 14px; }
.stop-line { width: 2px; flex: 1; min-height: 28px; margin-top: 2px; border-radius: 1px; }
.stop-line.blue { background: rgba(74,158,255,0.3); }
.stop-line.orange { background: rgba(255,107,53,0.3); }

.stop-center {
  flex: 1; padding: 12px 0 10px;
  border-bottom: 1px solid var(--border);
  display: flex; flex-direction: column; gap: 4px;
}
.stop-row:last-child .stop-center { border-bottom: none; }

.stop-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.stop-name { font-size: 15px; color: var(--text-primary); font-weight: 500; line-height: 1.3; flex: 1; }
.stop-name.terminal { font-weight: 700; font-size: 16px; color: var(--accent-green); }
.stop-num {
  font-size: 11px; color: var(--text-secondary);
  background: var(--bg-panel); border-radius: 8px;
  padding: 1px 6px; flex-shrink: 0; font-family: var(--font-mono);
}
.vehicle-row { display: flex; align-items: center; }
.vehicle-pill {
  font-size: 12px; color: #ff6b35;
  background: rgba(255,107,53,0.1); border: 1px solid rgba(255,107,53,0.3);
  border-radius: 12px; padding: 2px 8px; font-weight: 600;
}
.stop-dist { font-size: 12px; color: var(--text-secondary); }

/* Панель маршрутов через остановку */
.stop-routes-panel {
  margin-top: 10px; padding: 12px;
  background: var(--bg-panel); border-radius: 12px;
  border: 1px solid rgba(0,200,150,0.2);
}
.routes-loading { font-size: 13px; color: var(--text-secondary); }
.routes-panel-label { font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; }
.routes-panel-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.route-chip {
  background: var(--bg-card); border: 1px solid var(--border);
  color: var(--accent-green); font-family: var(--font-mono);
  font-size: 13px; font-weight: 700; padding: 5px 12px;
  border-radius: 8px; cursor: pointer; transition: all 0.15s;
}
.route-chip:hover { background: var(--accent-green); color: #000; border-color: var(--accent-green); }
.route-chip.current {
  background: rgba(0,200,150,0.15); border-color: var(--accent-green);
  cursor: default;
}
.routes-empty { font-size: 13px; color: var(--text-secondary); }

.stop-right { padding-top: 13px; flex-shrink: 0; min-width: 52px; text-align: right; }
.eta-val { font-size: 12px; color: var(--accent-green); font-weight: 700; }
.eta-min { font-size: 15px; color: #4a9eff; font-weight: 700; font-family: var(--font-mono); }
.eta-unit { font-size: 10px; font-weight: 400; margin-left: 1px; font-family: var(--font-main); }
.eta-km { font-size: 10px; color: var(--text-secondary); font-family: var(--font-mono); display: block; text-align: right; margin-top: 2px; }
.eta-bus { font-size: 16px; display: block; text-align: right; opacity: 0.5; }
.eta-now { font-size: 12px; color: #ff6b35; font-weight: 700; animation: blink 1s infinite; }

.empty-state { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text-secondary); font-size: 15px; }
</style>
