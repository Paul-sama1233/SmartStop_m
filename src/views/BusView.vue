<template>
  <div class="page">

    <!-- Поиск -->
    <div class="search-bar">
      <span class="search-icon">🔍</span>
      <input
        v-model="searchQuery"
        placeholder="Номер маршрута..."
      />
      <button v-if="searchQuery" class="clear-btn" @click="searchQuery = ''">✕</button>
    </div>

    <!-- Список маршрутов -->
    <div class="list-content">
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
            <span class="meta-item" v-if="bus.vehicle_count > 0">🚌 {{ bus.vehicle_count }} авт.</span>
            <span class="meta-item" v-if="bus.active_vehicles > 0">
              <span class="online-dot"></span>{{ bus.active_vehicles }} в пути
            </span>
            <span class="meta-item" v-if="bus.avg_trip_minutes">⏱ {{ bus.avg_trip_minutes }} мин</span>
          </div>
        </div>

        <div class="bus-card-arrow">›</div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/index.js'

const router = useRouter()
const searchQuery = ref('')
const busesData = ref([])

const filteredBuses = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  let list = q
    ? busesData.value.filter(b => b.number.toLowerCase().includes(q))
    : [...busesData.value]
  list.sort((a, b) => {
    if (b.is_favorite !== a.is_favorite) return b.is_favorite ? 1 : -1
    if (b.vehicle_count !== a.vehicle_count) return b.vehicle_count - a.vehicle_count
    const na = parseInt(a.number), nb = parseInt(b.number)
    if (!isNaN(na) && !isNaN(nb)) return na - nb
    return a.number.localeCompare(b.number)
  })
  return list
})

onMounted(async () => {
  const boardResp = await api.getBoard()
  busesData.value = boardResp.data.buses
})

function selectBus(bus) {
  router.push(`/route/${bus.number}`)
}

function formatEndpoint(name, part) {
  if (!name) return ''
  const parts = name.split('-')
  if (parts.length < 2) return name
  return part === 'start' ? parts[0].trim() : parts[parts.length - 1].trim()
}
</script>

<style scoped>
.page {
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
  padding: 16px 20px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.search-icon { font-size: 22px; }
.search-bar input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 18px;
  font-family: var(--font-main);
}
.search-bar input::placeholder { color: var(--text-secondary); }
.clear-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 20px;
}

.list-content { flex: 1; overflow-y: auto; }
.empty-state {
  text-align: center;
  padding: 40px 16px;
  color: var(--text-secondary);
  font-size: 15px;
}

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
  width: 48px;
  height: 48px;
  background: var(--bg-panel);
  border-radius: 10px;
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
}
.bus-number {
  font-size: 20px;
  font-weight: 800;
  color: var(--accent-green);
  font-family: var(--font-mono);
}
.fav-star { font-size: 12px; }

.bus-card-right {
  flex: 1;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow: hidden;
}
.bus-route-names { display: flex; flex-direction: column; gap: 3px; }
.bus-route-a {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.bus-route-b {
  font-size: 16px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.bus-card-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.meta-item {
  font-size: 15px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}
.online-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent-green);
  box-shadow: 0 0 5px var(--accent-green);
  display: inline-block;
}
.bus-card-arrow {
  display: flex;
  align-items: center;
  padding: 0 14px;
  color: var(--text-secondary);
  font-size: 24px;
  flex-shrink: 0;
}
</style>
