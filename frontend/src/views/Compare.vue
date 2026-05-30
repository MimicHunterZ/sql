<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import CompareChart from '../components/CompareChart.vue'
import { getCompare } from '../api'

// ── Available games (matches steamcharts_history.json keys) ──────────────────
const GAME_LIST = [
  { appid: '730',     name: 'Counter-Strike 2' },
  { appid: '570',     name: 'Dota 2' },
  { appid: '578080',  name: 'PUBG' },
  { appid: '271590',  name: 'GTA V' },
  { appid: '252490',  name: 'Rust' },
  { appid: '1172470', name: 'Apex Legends' },
  { appid: '440',     name: 'Team Fortress 2' },
  { appid: '1086940', name: "Baldur's Gate 3" },
  { appid: '1245620', name: 'Elden Ring' },
  { appid: '2399830', name: 'Helldivers 2' },
  { appid: '1091500', name: 'Cyberpunk 2077' },
  { appid: '252950',  name: 'Rocket League' },
  { appid: '1599340', name: 'Lost Ark' },
  { appid: '381210',  name: 'Dead by Daylight' },
  { appid: '550',     name: 'Left 4 Dead 2' },
  { appid: '346110',  name: 'ARK: Survival Evolved' },
  { appid: '359550',  name: 'Rainbow Six Siege' },
]

const COLORS = ['#60a5fa', '#a78bfa', '#34d399', '#f472b6', '#fbbf24']

const MAX_SELECT = 5

const selected  = ref(['730', '570', '578080'])   // default: top 3
const loading   = ref(false)
const chartData = ref([])   // [{ name, history }]

function fmtNum(n) {
  if (n == null) return '--'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + 'M'
  if (n >= 1_000)     return (n / 1_000).toFixed(1) + 'K'
  return Number(n).toLocaleString()
}

function latestAvg(history) {
  if (!history || !history.length) return '--'
  // history is already oldest→newest from API (reversed)
  const rows = [...history].sort((a, b) => {
    const months = ['January','February','March','April','May','June',
                    'July','August','September','October','November','December']
    const parse = s => {
      const [mon, yr] = s.split(' ')
      return Number(yr) * 12 + months.indexOf(mon)
    }
    return parse(b.month) - parse(a.month)
  })
  return fmtNum(rows[0]?.avg_players)
}

async function fetchCompare() {
  if (!selected.value.length) { chartData.value = []; return }
  loading.value = true
  try {
    const result = await getCompare(selected.value)
    chartData.value = result
  } catch (e) {
    console.error(e)
    chartData.value = []
  } finally {
    loading.value = false
  }
}

function toggle(appid) {
  const idx = selected.value.indexOf(appid)
  if (idx === -1) {
    if (selected.value.length >= MAX_SELECT) return
    selected.value = [...selected.value, appid]
  } else {
    selected.value = selected.value.filter(id => id !== appid)
  }
}

const isSelected = appid => selected.value.includes(appid)
const atMax      = computed(() => selected.value.length >= MAX_SELECT)

watch(selected, fetchCompare, { deep: true })
onMounted(fetchCompare)
</script>

<template>
  <div class="compare-page">

    <div class="page-header">
      <div>
        <h1 class="page-title">游戏 CCU 对比</h1>
        <p class="page-sub">17 款热门游戏 · 最多同时对比 {{ MAX_SELECT }} 款 · 历史月度同时在线人数</p>
      </div>
    </div>

    <div class="compare-layout">

      <!-- game picker -->
      <div class="glass-card picker-card">
        <p class="section-label">选择游戏</p>
        <p class="picker-hint" v-if="atMax">已达上限（{{ MAX_SELECT }} 款）</p>

        <div class="game-list">
          <button
            v-for="g in GAME_LIST"
            :key="g.appid"
            class="picker-item"
            :class="{
              'picker-item--on':       isSelected(g.appid),
              'picker-item--disabled': atMax && !isSelected(g.appid)
            }"
            @click="toggle(g.appid)"
          >
            <span class="picker-check">{{ isSelected(g.appid) ? '✓' : '' }}</span>
            <img
              :src="`https://cdn.akamai.steamstatic.com/steam/apps/${g.appid}/capsule_sm_120.jpg`"
              :alt="g.name"
              class="picker-cover"
              loading="lazy"
            />
            <span class="picker-name">{{ g.name }}</span>
          </button>
        </div>

        <div class="selected-summary">
          <span v-for="id in selected" :key="id" class="sel-badge">
            {{ GAME_LIST.find(g => g.appid === id)?.name }}
          </span>
        </div>
      </div>

      <!-- chart -->
      <div class="glass-card chart-card">
        <p class="section-label">月度平均在线人数趋势</p>
        <div v-if="loading" class="loading-msg">加载中...</div>
        <CompareChart v-else :games="chartData" />
      </div>

    </div>

    <!-- stat strip -->
    <div class="stat-strip" v-if="chartData.length && !loading">
      <div
        v-for="(g, i) in chartData"
        :key="g.name"
        class="glass-card stat-mini"
      >
        <div class="stat-mini-dot" :style="{ background: COLORS[i % COLORS.length], boxShadow: `0 0 8px ${COLORS[i % COLORS.length]}` }"></div>
        <div>
          <p class="stat-mini-name">{{ g.name }}</p>
          <p class="stat-mini-val">
            {{ latestAvg(g.history) }}
            <span class="stat-mini-unit">近期月均</span>
          </p>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.compare-page { display: flex; flex-direction: column; gap: 20px; }

.compare-layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 16px;
  align-items: start;
}

.picker-card { padding: 20px; }
.picker-hint { font-size: 10px; color: #f472b6; margin-bottom: 8px; letter-spacing: .05em; }

.game-list { display: flex; flex-direction: column; gap: 6px; }

.picker-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: rgba(0,0,0,.2);
  color: #9ca3af;
  font-size: 12px;
  cursor: pointer;
  transition: all .15s;
  text-align: left;
  width: 100%;
}
.picker-cover {
  width: 48px;
  height: 22px;
  object-fit: cover;
  border-radius: 3px;
  border: 1px solid rgba(255,255,255,.07);
  flex-shrink: 0;
}
.picker-item:hover:not(.picker-item--disabled) {
  border-color: rgba(96,165,250,.3);
  color: #d1d5db;
  background: rgba(96,165,250,.07);
}
.picker-item--on {
  border-color: rgba(96,165,250,.5);
  background: rgba(96,165,250,.12);
  color: var(--blue);
}
.picker-item--disabled { opacity: .4; cursor: not-allowed; }

.picker-check {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(96,165,250,.4);
  border-radius: 4px;
  font-size: 10px;
  color: var(--blue);
  flex-shrink: 0;
}
.picker-name { font-weight: 500; }

.selected-summary {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.sel-badge {
  display: inline-block;
  padding: 2px 8px;
  background: rgba(96,165,250,.12);
  border: 1px solid rgba(96,165,250,.3);
  border-radius: 999px;
  font-size: 10px;
  color: #93c5fd;
}

.chart-card { padding: 20px; }
.loading-msg { text-align:center; padding:80px; color:#6b7280; font-size:13px; }

/* stat strip */
.stat-strip {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.stat-mini {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  flex: 1;
  min-width: 160px;
}
.stat-mini-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.stat-mini-name { font-size: 11px; color: #9ca3af; margin-bottom: 3px; }
.stat-mini-val  {
  font-family: 'Rajdhani', sans-serif;
  font-size: 16px;
  font-weight: 700;
  color: var(--cyan);
}
.stat-mini-unit { font-size: 10px; color: #6b7280; font-family: 'Inter', sans-serif; margin-left: 4px; }
</style>
