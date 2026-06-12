<template>
  <div class="lines-page">
    <!-- Поиск -->
    <div class="lines-search">
      <span>🔍</span>
      <input v-model="searchQuery" placeholder="Поиск маршрута..." />
    </div>

    <!-- Фильтры -->
    <div class="filters">
      <button
        v-for="f in filters"
        :key="f.key"
        class="filter-btn"
        :class="{ active: activeFilter === f.key }"
        @click="activeFilter = f.key"
      >{{ f.label }}</button>
    </div>

    <!-- Список -->
    <div class="lines-list">
      <div
        v-for="bus in filteredBuses"
        :key="bus.number"
        class="line-card"
        @click="$router.push('/stations')"
      >
        <span class="line-badge">{{ bus.number }}</span>
        <div class="line-info">
          <span class="line-name-a">→ {{ formatEndpoint(bus.name, 'start') }}</span>
          <span class="line-name-b">→ {{ formatEndpoint(bus.name, 'end') }}</span>
          <div class="line-meta">
            <span>🚌 {{ bus.active_vehicles || 0 }} в пути</span>
            <span class="line-type">{{ formatType(bus.transport_type) }}</span>
          </div>
        </div>
        <span class="line-arrow">›</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/router_index.js'

const searchQuery = ref('')
const activeFilter = ref('all')
const busesData = ref([])

const filters = [
  { key: 'all', label: 'Все' },
  { key: 'bus', label: 'Автобус' },
  { key: 'magistral', label: 'Магистраль' },
  { key: 'halqa', label: 'Кольцевые' },
]

onMounted(async () => {
  const resp = await api.getBoard()
  busesData.value = resp.data.buses
})

const filteredBuses = computed(() => {
  let list = busesData.value
  const q = searchQuery.value.toLowerCase()

  if (q) {
    list = list.filter(b =>
      b.number.toLowerCase().includes(q) ||
      b.name.toLowerCase().includes(q)
    )
  }

  if (activeFilter.value === 'magistral') {
    list = list.filter(b => b.transport_type?.toLowerCase().includes('magistral'))
  } else if (activeFilter.value === 'halqa') {
    list = list.filter(b => b.transport_type?.toLowerCase().includes('halqa'))
  } else if (activeFilter.value === 'bus') {
    list = list.filter(b => b.transport_type?.toLowerCase().includes('avtobus'))
  }

  return list
})

function formatEndpoint(name, part) {
  const parts = name.split('-')
  if (parts.length < 2) return name
  return part === 'start' ? parts[0].trim() : parts[parts.length - 1].trim()
}

function formatType(type) {
  if (!type) return ''
  if (type.toLowerCase().includes('magistral')) return '🔵 Магистраль'
  if (type.toLowerCase().includes('halqa')) return '🔄 Кольцевой'
  if (type.toLowerCase().includes('yetkazib')) return '📦 Подвозящий'
  return '🚌 Автобус'
}
</script>

<style scoped>
.lines-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  background: var(--bg-dark);
}

.lines-search {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.lines-search input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 15px;
  font-family: var(--font-main);
}

.lines-search input::placeholder { color: var(--text-secondary); }

.filters {
  display: flex;
  gap: 8px;
  padding: 10px 16px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  overflow-x: auto;
  flex-shrink: 0;
}

.filters::-webkit-scrollbar { display: none; }

.filter-btn {
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  font-family: var(--font-main);
  transition: all 0.2s;
}

.filter-btn.active {
  background: var(--accent-green);
  border-color: var(--accent-green);
  color: #000;
}

.lines-list {
  flex: 1;
  overflow-y: auto;
}

.line-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.15s;
}

.line-card:hover { background: rgba(255,255,255,0.03); }

.line-badge {
  min-width: 52px;
  height: 52px;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 800;
  color: var(--accent-green);
  font-family: var(--font-mono);
  flex-shrink: 0;
  padding: 0 8px;
}

.line-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  overflow: hidden;
}

.line-name-a, .line-name-b {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.line-name-a { color: var(--text-primary); font-weight: 600; }
.line-name-b { color: var(--text-secondary); }

.line-meta {
  display: flex;
  gap: 10px;
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.line-type {
  color: var(--accent-blue);
}

.line-arrow {
  color: var(--text-secondary);
  font-size: 20px;
  flex-shrink: 0;
}
</style>
