<template>
  <div class="app-shell">

    <!-- Вертикальное меню слева -->
    <nav class="sidebar">
      <div class="sidebar-logo">
        <span class="logo-icon">🚍</span>
      </div>

      <RouterLink to="/bus" class="nav-item" :class="{ active: route.path === '/bus' || route.path.startsWith('/route') }">
        <span class="nav-icon">🚌</span>
        <span class="nav-label">Автобус</span>
      </RouterLink>

      <RouterLink to="/metro" class="nav-item" :class="{ active: route.path === '/metro' }">
        <span class="nav-icon">🚇</span>
        <span class="nav-label">Метро</span>
      </RouterLink>

      <RouterLink to="/map" class="nav-item" :class="{ active: route.path === '/map' }">
        <span class="nav-icon">🗺️</span>
        <span class="nav-label">Карта</span>
      </RouterLink>
    </nav>

    <!-- Контент -->
    <div class="main-content">
      <RouterView />
    </div>

  </div>
</template>

<script setup>
import { RouterView, RouterLink, useRoute } from 'vue-router'
const route = useRoute()
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --bg-dark: #0f0f1a;
  --bg-card: #1a1a2e;
  --bg-panel: #16213e;
  --accent-green: #00c896;
  --accent-orange: #ff6b35;
  --accent-blue: #4a9eff;
  --text-primary: #ffffff;
  --text-secondary: #8892a4;
  --border: rgba(255,255,255,0.08);
  --font-main: 'Nunito', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

body {
  font-family: var(--font-main);
  background: var(--bg-dark);
  color: var(--text-primary);
  overflow: hidden;
  height: 100vh;
}

.app-shell {
  display: flex;
  flex-direction: row;
  height: 100vh;
  position: relative;
}

.sidebar {
  width: 88px;
  flex-shrink: 0;
  background: var(--bg-card);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 0;
  gap: 6px;
  z-index: 100;
}

.sidebar-logo {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--bg-panel);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
  flex-shrink: 0;
}
.logo-icon { font-size: 26px; }

.nav-item {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  padding: 12px 4px;
  text-decoration: none;
  color: var(--text-secondary);
  transition: all 0.2s;
  cursor: pointer;
  border-radius: 12px;
  position: relative;
}

.nav-item:hover {
  color: var(--text-primary);
  background: rgba(255,255,255,0.03);
}

.nav-item.active { color: var(--accent-green); }

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 28px;
  background: var(--accent-green);
  border-radius: 0 3px 3px 0;
}

.nav-icon { font-size: 24px; line-height: 1; }
.nav-label { font-size: 12px; font-weight: 700; letter-spacing: 0.2px; }

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.metro-map-dot {
  width: 14px; height: 14px; border-radius: 50%;
  border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}
.metro-map-dot.selected { width: 16px; height: 16px; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 4px; }
</style>
