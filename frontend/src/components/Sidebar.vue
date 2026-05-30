<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { triggerIngest } from '../api'

const router   = useRouter()
const syncing  = ref(false)
const syncMsg  = ref('')

const navItems = [
  { to: '/',        icon: '📊', label: '总览' },
  { to: '/compare', icon: '⚔️', label: '对比' },
  { to: '/market',  icon: '💰', label: '市场' },
]

async function doSync() {
  syncing.value = true
  syncMsg.value = ''
  try {
    await triggerIngest()
    syncMsg.value = '✓'
    setTimeout(() => { syncMsg.value = '' }, 3000)
  } catch {
    syncMsg.value = '✗'
  } finally {
    syncing.value = false
  }
}
</script>

<template>
  <nav class="sidebar-nav">
    <!-- logo -->
    <div class="nav-logo">
      <span class="logo-icon">🎮</span>
    </div>

    <!-- nav items -->
    <div class="nav-items">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        active-class="nav-item--active"
        :exact="item.to === '/'"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-tooltip">{{ item.label }}</span>
      </RouterLink>
    </div>

    <!-- sync button at bottom -->
    <div class="nav-bottom">
      <button class="nav-item nav-sync" @click="doSync" :disabled="syncing" :title="syncing ? '同步中...' : '同步数据'">
        <span class="nav-icon" :class="{ spinning: syncing }">⟳</span>
        <span class="nav-tooltip">{{ syncMsg || (syncing ? '同步中' : '同步') }}</span>
      </button>
    </div>
  </nav>
</template>

<style scoped>
.sidebar-nav {
  width: var(--sidebar-w);
  min-height: 100vh;
  background: rgba(10, 10, 26, 0.95);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 0;
  position: sticky;
  top: 0;
  z-index: 100;
  flex-shrink: 0;
}

.nav-logo {
  padding: 10px 0 18px;
  border-bottom: 1px solid var(--border);
  width: 100%;
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
}
.logo-icon { font-size: 22px; }

.nav-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  width: 100%;
  padding: 0 8px;
  align-items: center;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: 1px solid transparent;
  background: transparent;
  color: #6b7280;
  text-decoration: none;
  cursor: pointer;
  transition: all .2s;
  font-size: 12px;
}
.nav-item:hover {
  background: rgba(96,165,250,.1);
  border-color: rgba(96,165,250,.3);
  color: var(--blue);
}
.nav-item--active {
  background: linear-gradient(135deg, rgba(96,165,250,.2), rgba(167,139,250,.15));
  border-color: rgba(96,165,250,.5);
  color: var(--blue);
  box-shadow: 0 0 16px rgba(96,165,250,.25);
}

.nav-icon { font-size: 18px; line-height: 1; }

/* tooltip on hover */
.nav-tooltip {
  position: absolute;
  left: calc(100% + 10px);
  background: rgba(17,24,39,.95);
  border: 1px solid var(--border);
  color: #e0e0e0;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .05em;
  padding: 4px 10px;
  border-radius: 8px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity .15s;
  z-index: 200;
}
.nav-item:hover .nav-tooltip { opacity: 1; }

.nav-bottom {
  padding: 0 8px;
  width: 100%;
  display: flex;
  justify-content: center;
  border-top: 1px solid var(--border);
  padding-top: 12px;
  margin-top: 8px;
}

.nav-sync { border: none; }

@keyframes spin { to { transform: rotate(360deg); } }
.spinning { animation: spin .8s linear infinite; display: inline-block; }
</style>
