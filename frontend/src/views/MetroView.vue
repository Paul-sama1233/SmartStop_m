<template>
  <div class="page">

    <!-- Поиск -->
    <div class="search-bar">
      <span class="search-icon">🔍</span>
      <input v-model="searchQuery" placeholder="Станция метро..." />
      <button v-if="searchQuery" class="clear-btn" @click="searchQuery = ''">✕</button>
    </div>

    <!-- Карта — всегда открыта -->
    <div class="map-section">
      <div ref="mapContainer" class="map-container"></div>
      <div class="map-layer-btns">
        <button :class="{ active: mapLayer === 'map' }" @click="setLayer('map')">🗺</button>
        <button :class="{ active: mapLayer === 'satellite' }" @click="setLayer('satellite')">🛰</button>
      </div>
    </div>

    <!-- Панель ближайших остановок -->
    <div v-if="nearbyStation" class="nearby-panel">
      <div class="nearby-head">
        <div>
          <div class="nearby-title">🚌 Автобусы рядом</div>
          <div class="nearby-sub">{{ nearbyStation }} · радиус 150 м</div>
        </div>
        <button class="close-card" @click="clearNearby">✕</button>
      </div>
      <div v-if="nearbyStops.length > 0" class="nearby-list">
        <div v-for="s in nearbyStops" :key="s.id" class="nearby-stop">
          <div class="nearby-stop-info">
            <span class="nearby-stop-name">{{ s.name }}</span>
            <span class="nearby-stop-dist">{{ s.distance }} м</span>
          </div>
          <div class="nearby-routes">
            <span
              v-for="num in s.routes"
              :key="num"
              class="route-chip"
              @click="$router.push(`/route/${num}`)"
            >{{ num }}</span>
          </div>
        </div>
      </div>
      <div v-else class="nearby-empty">В радиусе 150 м нет автобусных остановок</div>
    </div>

    <!-- Список линий -->
    <div class="list-content" v-show="!nearbyStation">
      <div
        v-for="line in filteredMetro"
        :key="line.id"
        class="metro-row"
        :class="{ active: selectedLine?.id === line.id }"
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

      <div v-if="selectedLine" class="tip">
        💡 Нажмите на станцию на карте — покажу ближайшие автобусные остановки
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import api from '../api/index.js'

const mapContainer = ref(null)
const searchQuery = ref('')
const mapLayer = ref('map')
const metroLines = ref([])
const selectedLine = ref(null)
const nearbyStops = ref([])
const nearbyStation = ref('')

let map = null
let tileLayer = null
let metroMarkers = []
let nearbyMarkers = []

const LAYERS = {
  map: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
}

const filteredMetro = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return metroLines.value
  return metroLines.value.filter(line =>
    line.name.toLowerCase().includes(q) ||
    line.stations?.some(s => s.name.toLowerCase().includes(q))
  )
})

onMounted(async () => {
  map = L.map(mapContainer.value, { zoomControl: false }).setView([41.2995, 69.2401], 12)
  tileLayer = L.tileLayer(LAYERS.map, { attribution: '© OpenStreetMap' }).addTo(map)

  const boardResp = await api.getBoard()
  metroLines.value = boardResp.data.metro

  // Сразу рисуем все ветки метро
  drawAllLines()
})

onUnmounted(() => { if (map) map.remove() })

function setLayer(type) {
  mapLayer.value = type
  if (tileLayer) map.removeLayer(tileLayer)
  tileLayer = L.tileLayer(LAYERS[type], {
    attribution: type === 'map' ? '© OpenStreetMap' : '© Esri'
  }).addTo(map)
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

function clearNearbyMarkers() {
  nearbyMarkers.forEach(m => map.removeLayer(m))
  nearbyMarkers = []
}

// Рисуем ВСЕ ветки метро на карте
function drawAllLines() {
  clearMetroMarkers()
  const allCoords = []

  metroLines.value.forEach(line => {
    const points = buildLinePoints(line)
    if (points.length > 1) {
      metroMarkers.push(
        L.polyline(points, {
          color: line.color, weight: 5, opacity: 0.85, smoothFactor: 1.5
        }).addTo(map)
      )
    }

    line.stations?.forEach((s, i) => {
      if (!s.latitude) return
      allCoords.push([s.latitude, s.longitude])
      const isTerminal = i === 0 || i === line.stations.length - 1
      const icon = L.divIcon({
        className: '',
        html: `<div style="
          width:${isTerminal?16:12}px;
          height:${isTerminal?16:12}px;
          border-radius:50%;
          background:${isTerminal ? line.color : 'white'};
          border:3px solid ${line.color};
          box-shadow:0 2px 6px rgba(0,0,0,0.4);
          cursor:pointer
        "></div>`,
        iconSize: [isTerminal?16:12, isTerminal?16:12],
        iconAnchor: [isTerminal?8:6, isTerminal?8:6],
      })
      const m = L.marker([s.latitude, s.longitude], { icon }).addTo(map)
      m.bindTooltip(s.name, { direction: 'top' })
      m.on('click', () => loadNearby(s, line))
      metroMarkers.push(m)
    })
  })

  // Подгоняем карту под все ветки
  if (allCoords.length > 0) {
    try { map.fitBounds(L.latLngBounds(allCoords), { padding: [30, 30] }) } catch (e) {}
  }
}

function selectMetro(line) {
  selectedLine.value = line
  clearNearby()
  clearMetroMarkers()

  const coords = []
  const points = buildLinePoints(line)

  // Рисуем все ветки, выбранную — ярче
  metroLines.value.forEach(l => {
    const pts = buildLinePoints(l)
    const isSelected = l.id === line.id
    if (pts.length > 1) {
      metroMarkers.push(
        L.polyline(pts, {
          color: l.color,
          weight: isSelected ? 6 : 3,
          opacity: isSelected ? 0.95 : 0.3,
          smoothFactor: 1.5,
        }).addTo(map)
      )
    }
    l.stations?.forEach((s, i) => {
      if (!s.latitude) return
      const isSelected2 = l.id === line.id
      const isTerminal = i === 0 || i === l.stations.length - 1
      const icon = L.divIcon({
        className: '',
        html: `<div style="
          width:${isTerminal?16:12}px;
          height:${isTerminal?16:12}px;
          border-radius:50%;
          background:${isTerminal ? l.color : 'white'};
          border:3px solid ${l.color};
          box-shadow:0 2px 6px rgba(0,0,0,0.4);
          cursor:pointer;
          opacity:${isSelected2 ? 1 : 0.3}
        "></div>`,
        iconSize: [isTerminal?16:12, isTerminal?16:12],
        iconAnchor: [isTerminal?8:6, isTerminal?8:6],
      })
      const m = L.marker([s.latitude, s.longitude], { icon }).addTo(map)
      if (isSelected2) {
        m.bindTooltip(s.name, { direction: 'top' })
        m.on('click', () => loadNearby(s, l))
        coords.push([s.latitude, s.longitude])
      }
      metroMarkers.push(m)
    })
  })

  if (coords.length > 0) {
    try { map.fitBounds(L.latLngBounds(coords), { padding: [50, 50] }) } catch (e) {}
  }
}

async function loadNearby(station, line) {
  nearbyStation.value = station.name
  clearNearbyMarkers()

  map.setView([station.latitude, station.longitude], 16, { animate: true })

  const stationIcon = L.divIcon({
    className: '',
    html: `<div style="background:${line.color};color:white;font-weight:800;font-size:11px;padding:4px 8px;border-radius:8px;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.5);white-space:nowrap">Ⓜ ${station.name}</div>`,
    iconSize: [0, 0], iconAnchor: [0, 0],
  })
  nearbyMarkers.push(L.marker([station.latitude, station.longitude], { icon: stationIcon, zIndexOffset: 1000 }).addTo(map))

  nearbyMarkers.push(L.circle([station.latitude, station.longitude], {
    radius: 150, color: '#ff6b35', fillColor: '#ff6b35', fillOpacity: 0.08, weight: 1,
  }).addTo(map))

  try {
    const resp = await api.getNearbyStops(station.latitude, station.longitude, 150)
    nearbyStops.value = resp.data.stops || []

    nearbyStops.value.forEach(s => {
      const icon = L.divIcon({
        className: '',
        html: `<div style="background:#ff6b35;color:white;font-size:10px;font-weight:800;width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.4)">🚌</div>`,
        iconSize: [26, 26], iconAnchor: [13, 13],
      })
      const m = L.marker([s.latitude, s.longitude], { icon }).addTo(map)
      m.bindPopup(`
        <div style="font-family:sans-serif;min-width:140px">
          <div style="font-weight:700;font-size:13px">${s.name}</div>
          <div style="color:#888;font-size:11px">${s.distance} м от метро</div>
          <div style="margin-top:4px;font-size:12px">Маршруты: <b>${s.routes.join(', ')}</b></div>
        </div>
      `)
      nearbyMarkers.push(m)
    })
  } catch (e) {
    console.error(e)
    nearbyStops.value = []
  }
}

function clearNearby() {
  nearbyStation.value = ''
  nearbyStops.value = []
  clearNearbyMarkers()
}
</script>

<style scoped>
.page { display: flex; flex-direction: column; flex: 1; overflow: hidden; background: var(--bg-dark); }

.search-bar {
  display: flex; align-items: center; gap: 20px;
  padding: 18px 20px; background: var(--bg-card);
  border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.search-icon { font-size: 25px; }
.search-bar input {
  flex: 1; background: none; border: none; outline: none;
  color: var(--text-primary); font-size: 20px; font-family: var(--font-main);
}
.search-bar input::placeholder { color: var(--text-secondary); }
.clear-btn { background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 20px; }

/* Карта всегда открыта — фиксированная высота */
.map-section {
  height: 55vh;
  flex-shrink: 0;
  position: relative;
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

/* Панель ближайших остановок */
.nearby-panel { flex: 1; overflow-y: auto; display: flex; flex-direction: column; }
.nearby-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; background: rgba(255,107,53,0.08);
  border-bottom: 1px solid rgba(255,107,53,0.2);
  position: sticky; top: 0; z-index: 1;
}
.nearby-title { font-size: 15px; font-weight: 800; color: var(--accent-orange); }
.nearby-sub { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.close-card { background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 18px; }

.nearby-list { display: flex; flex-direction: column; }
.nearby-stop {
  padding: 14px 16px; border-bottom: 1px solid var(--border);
  display: flex; flex-direction: column; gap: 8px;
}
.nearby-stop-info { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.nearby-stop-name { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.nearby-stop-dist {
  font-size: 12px; color: var(--accent-orange); flex-shrink: 0;
  background: rgba(255,107,53,0.1); padding: 2px 8px; border-radius: 10px;
}
.nearby-routes { display: flex; flex-wrap: wrap; gap: 6px; }
.route-chip {
  background: var(--bg-panel); border: 1px solid var(--border);
  color: var(--accent-green); font-family: var(--font-mono);
  font-size: 14px; font-weight: 700; padding: 4px 12px;
  border-radius: 8px; cursor: pointer; transition: all 0.15s;
}
.route-chip:hover { background: var(--accent-green); color: #000; border-color: var(--accent-green); }
.nearby-empty { padding: 30px 16px; text-align: center; color: var(--text-secondary); font-size: 14px; }

.list-content { flex: 1; overflow-y: auto; }
.metro-row {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; border-bottom: 1px solid var(--border);
  cursor: pointer; transition: background 0.15s;
}
.metro-row:hover, .metro-row.active { background: rgba(255,255,255,0.04); }
.metro-color-dot { width: 16px; height: 16px; border-radius: 50%; flex-shrink: 0; }
.row-info { flex: 1; display: flex; flex-direction: column; gap: 3px; overflow: hidden; }
.row-name { font-size: 15px; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.row-name.muted { color: var(--text-secondary); font-weight: 400; font-size: 13px; }
.metro-count { font-size: 12px; color: var(--text-secondary); flex-shrink: 0; }

.tip {
  margin: 16px; padding: 12px 14px; font-size: 13px; line-height: 1.4;
  color: var(--text-secondary); background: rgba(74,158,255,0.08);
  border: 1px solid rgba(74,158,255,0.2); border-radius: 12px;
}
</style>
