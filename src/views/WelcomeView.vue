<template>
  <div class="welcome-page">
    <!-- Фоновое изображение -->
    <div class="hero-bg">
      <div class="hero-overlay"></div>
      <div class="hero-content">
        <h1 class="app-title">SmartStop</h1>
        <p class="app-subtitle">Умные остановки Ташкента</p>
      </div>
    </div>

    <!-- Строка поиска -->
    <div class="search-section">
      <div class="search-bar" @click="$router.push('/lines')">
        <span class="search-icon">🔍</span>
        <span class="search-placeholder">Куда вы хотите поехать?</span>
        <button class="search-btn">→</button>
      </div>
    </div>

    <!-- Уведомление о геолокации -->
    <div class="location-banner" v-if="!locationGranted">
      <span class="location-icon">📍</span>
      <p>Разрешите доступ к геолокации для точной информации о маршрутах</p>
      <button class="location-btn" @click="requestLocation">Разрешить</button>
    </div>

    <!-- Скроллируемый контент -->
    <div class="welcome-content">
      <!-- Избранные -->
      <div class="section">
        <div class="section-header">
          <span class="section-title">Избранное</span>
          <button class="section-action" @click="showAddFavorite = true">+ Добавить</button>
        </div>

        <div class="favorite-item" @click="setDestination('home')">
          <div class="fav-icon home">🏠</div>
          <div class="fav-info">
            <span class="fav-name">Дом</span>
            <span class="fav-hint" v-if="!favorites.home">Нажмите чтобы установить</span>
            <span class="fav-hint" v-else>{{ favorites.home }}</span>
          </div>
          <span class="fav-arrow">›</span>
        </div>

        <div class="divider"></div>

        <div class="favorite-item" @click="setDestination('work')">
          <div class="fav-icon work">💼</div>
          <div class="fav-info">
            <span class="fav-name">Работа</span>
            <span class="fav-hint" v-if="!favorites.work">Нажмите чтобы установить</span>
            <span class="fav-hint" v-else>{{ favorites.work }}</span>
          </div>
          <span class="fav-arrow">›</span>
        </div>
      </div>

      <!-- Быстрые действия -->
      <div class="section">
        <div class="quick-actions">
          <div class="quick-card" @click="$router.push('/stations')">
            <span class="quick-icon">🚌</span>
            <span class="quick-label">Ближайшие остановки</span>
          </div>
          <div class="quick-card" @click="$router.push('/lines')">
            <span class="quick-icon">🗺️</span>
            <span class="quick-label">Все маршруты</span>
          </div>
          <div class="quick-card metro" @click="$router.push('/stations?tab=metro')">
            <span class="quick-icon">🚇</span>
            <span class="quick-label">Метро</span>
          </div>
          <div class="quick-card taxi" @click="openTaxi">
            <span class="quick-icon">🚕</span>
            <span class="quick-label">Такси</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Модалка добавления избранного -->
    <div class="modal-overlay" v-if="showAddFavorite" @click.self="showAddFavorite = false">
      <div class="modal">
        <h3>Установить адрес</h3>
        <div class="modal-options">
          <button class="modal-btn" @click="editFavorite('home')">🏠 Дом</button>
          <button class="modal-btn" @click="editFavorite('work')">💼 Работа</button>
        </div>
        <button class="modal-close" @click="showAddFavorite = false">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const locationGranted = ref(false)
const showAddFavorite = ref(false)

const favorites = reactive({
  home: localStorage.getItem('fav_home') || '',
  work: localStorage.getItem('fav_work') || '',
})

function requestLocation() {
  navigator.geolocation.getCurrentPosition(
    () => { locationGranted.value = true },
    () => { locationGranted.value = false }
  )
}

function setDestination(type) {
  const address = prompt(`Введите адрес (${type === 'home' ? 'Дом' : 'Работа'}):`)
  if (address) {
    favorites[type] = address
    localStorage.setItem(`fav_${type}`, address)
  }
}

function editFavorite(type) {
  showAddFavorite.value = false
  setDestination(type)
}

function openTaxi() {
  window.open('https://redirect.appmetrica.yandex.com/route?utm_source=smartstop', '_blank')
}
</script>

<style scoped>
.welcome-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  background: var(--bg-dark);
}

/* Hero блок */
.hero-bg {
  position: relative;
  height: 220px;
  background: linear-gradient(135deg, #0f3460 0%, #16213e 50%, #0f0f1a 100%);
  flex-shrink: 0;
  overflow: hidden;
}

.hero-bg::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 50%, rgba(0,200,150,0.15) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(74,158,255,0.1) 0%, transparent 40%);
}

/* Анимированные круги */
.hero-bg::after {
  content: '';
  position: absolute;
  width: 300px;
  height: 300px;
  border: 1px solid rgba(0,200,150,0.1);
  border-radius: 50%;
  top: -100px;
  right: -100px;
  animation: pulse 4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.1); opacity: 1; }
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, transparent 40%, var(--bg-dark) 100%);
}

.hero-content {
  position: relative;
  z-index: 2;
  padding: 40px 20px 20px;
}

.app-title {
  font-size: 36px;
  font-weight: 800;
  color: var(--accent-green);
  letter-spacing: -1px;
  line-height: 1;
}

.app-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* Поиск */
.search-section {
  padding: 0 16px;
  margin-top: -24px;
  position: relative;
  z-index: 10;
  flex-shrink: 0;
}

.search-bar {
  display: flex;
  align-items: center;
  background: #ffffff;
  border-radius: 12px;
  padding: 14px 16px;
  gap: 10px;
  cursor: pointer;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}

.search-icon { font-size: 16px; }

.search-placeholder {
  flex: 1;
  color: #666;
  font-size: 15px;
  font-family: var(--font-main);
}

.search-btn {
  background: var(--accent-orange);
  color: white;
  border: none;
  border-radius: 8px;
  width: 36px;
  height: 36px;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Уведомление геолокации */
.location-banner {
  margin: 12px 16px 0;
  background: rgba(255,107,53,0.15);
  border: 1px solid rgba(255,107,53,0.3);
  border-radius: 12px;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.location-icon { font-size: 18px; flex-shrink: 0; }

.location-banner p {
  flex: 1;
  font-size: 12px;
  color: #ffb89a;
  line-height: 1.4;
}

.location-btn {
  background: var(--accent-orange);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  flex-shrink: 0;
  font-family: var(--font-main);
}

/* Контент */
.welcome-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Секции */
.section {
  background: var(--bg-card);
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--border);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px 8px;
}

.section-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-action {
  background: none;
  border: none;
  color: var(--accent-blue);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  font-family: var(--font-main);
}

/* Избранное */
.favorite-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 0.15s;
}

.favorite-item:hover { background: rgba(255,255,255,0.04); }

.fav-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.fav-icon.home { background: rgba(0,200,150,0.15); }
.fav-icon.work { background: rgba(74,158,255,0.15); }

.fav-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.fav-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.fav-hint {
  font-size: 12px;
  color: var(--text-secondary);
}

.fav-arrow {
  color: var(--text-secondary);
  font-size: 20px;
}

.divider {
  height: 1px;
  background: var(--border);
  margin: 0 16px;
}

/* Быстрые действия */
.quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: var(--border);
}

.quick-card {
  background: var(--bg-card);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.quick-card:hover { background: rgba(255,255,255,0.05); }

.quick-icon { font-size: 24px; }

.quick-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
}

.quick-card.metro .quick-icon { color: var(--accent-green); }
.quick-card.taxi .quick-icon { color: var(--accent-orange); }

/* Модалка */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  z-index: 1000;
  display: flex;
  align-items: flex-end;
}

.modal {
  background: var(--bg-card);
  border-radius: 20px 20px 0 0;
  padding: 24px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal h3 {
  font-size: 18px;
  font-weight: 700;
}

.modal-options {
  display: flex;
  gap: 12px;
}

.modal-btn {
  flex: 1;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  font-family: var(--font-main);
}

.modal-close {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 15px;
  padding: 8px;
  cursor: pointer;
  font-family: var(--font-main);
}
</style>
