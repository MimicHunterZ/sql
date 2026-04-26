<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import TrendChart from './components/TrendChart.vue'
import { getGames, getOverview, getPredict, getTrend, triggerIngest } from './api'

const loading = ref(false)
const errorMsg = ref('')
const games = ref([])
const overview = ref({ monitored_games: 0, warning: 'normal' })
const selectedGameId = ref(null)
const trend = ref([])
const predictPoints = ref([])
const discountRate = ref(20)
const updateQuality = ref(6)
const ingesting = ref(false)
const ingestMsg = ref('')
const selectedGame = computed(() => games.value.find((g) => g.appid === selectedGameId.value) || null)
let debounceTimer = null

function warningText(w) {
  if (w === 'high_peak_risk') return 'PEAK ALERT'
  if (w === 'attention') return 'ELEVATED'
  return 'NOMINAL'
}
function warningClass(w) {
  if (w === 'high_peak_risk') return 'text-red-400'
  if (w === 'attention') return 'text-yellow-400'
  return 'text-emerald-400'
}
function fmtNum(n) {
  if (n == null) return '--'
  return Number(n).toLocaleString()
}

async function runIngest() {
  ingesting.value = true
  ingestMsg.value = ''
  try {
    await triggerIngest()
    ingestMsg.value = 'SYNC INITIATED — refreshing in 35s'
    setTimeout(() => { refreshAll(); ingestMsg.value = '' }, 35000)
  } catch {
    ingestMsg.value = 'SYNC FAILED'
  } finally {
    ingesting.value = false
  }
}

async function loadTrendAndPredict() {
  if (!selectedGameId.value) return
  const trendResp = await getTrend(selectedGameId.value, 30)
  trend.value = trendResp.points
  try {
    const predResp = await getPredict(selectedGameId.value, discountRate.value, updateQuality.value)
    predictPoints.value = predResp.points
  } catch { predictPoints.value = [] }
}

async function refreshAll() {
  loading.value = true
  errorMsg.value = ''
  try {
    const [ov, gm] = await Promise.all([getOverview(), getGames()])
    overview.value = ov
    games.value = gm
    if (!selectedGameId.value && gm.length) selectedGameId.value = gm[0].appid
    await loadTrendAndPredict()
  } catch (err) {
    errorMsg.value = err?.response?.data?.detail || err?.message || 'LOAD ERROR'
  } finally {
    loading.value = false
  }
}

function debouncedPredict() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(async () => {
    if (!selectedGameId.value) return
    try {
      const r = await getPredict(selectedGameId.value, discountRate.value, updateQuality.value)
      predictPoints.value = r.points
    } catch { predictPoints.value = [] }
  }, 400)
}

watch(selectedGameId, loadTrendAndPredict)
watch([discountRate, updateQuality], debouncedPredict)
onMounted(refreshAll)
</script>

<template>
  <div class="terminal-root min-h-screen w-full">
    <!-- scanline overlay -->
    <div class="scanlines" aria-hidden="true"></div>

    <div class="mx-auto max-w-[1440px] px-5 py-5">

      <!-- HEADER -->
      <header class="mb-6 flex items-center justify-between border-b border-emerald-900/60 pb-4">
        <div class="flex items-center gap-4">
          <div class="status-dot"></div>
          <div>
            <h1 class="font-mono text-xl font-bold uppercase tracking-[0.2em] text-emerald-300">
              Steam CCU Intelligence
            </h1>
            <p class="font-mono text-[10px] tracking-widest text-emerald-700">
              LIVE · CONCURRENT USERS · PREDICTIVE ANALYTICS
            </p>
          </div>
        </div>
        <div class="flex flex-col items-end gap-1">
          <button
            @click="runIngest"
            :disabled="ingesting"
            class="sync-btn font-mono text-xs uppercase tracking-widest"
          >
            <span class="sync-icon">⟳</span>
            {{ ingesting ? 'SYNCING...' : 'SYNC DATA' }}
          </button>
          <span v-if="ingestMsg" class="font-mono text-[10px] text-emerald-600">{{ ingestMsg }}</span>
        </div>
      </header>

      <!-- STAT CARDS -->
      <section class="mb-6 grid grid-cols-3 gap-4">
        <div class="stat-card">
          <p class="card-label">MONITORED TARGETS</p>
          <p class="card-value">{{ overview.monitored_games || 0 }}</p>
          <p class="card-sub">active game feeds</p>
        </div>
        <div class="stat-card">
          <p class="card-label">HIGHEST ONLINE</p>
          <p class="card-value truncate text-2xl">{{ overview.top_game_name || '--' }}</p>
          <p class="card-sub">{{ fmtNum(overview.top_game_ccu) }} concurrent</p>
        </div>
        <div class="stat-card">
          <p class="card-label">SYSTEM STATUS</p>
          <p class="card-value text-2xl" :class="warningClass(overview.warning)">
            {{ warningText(overview.warning) }}
          </p>
          <p class="card-sub">prediction confidence: HIGH</p>
        </div>
      </section>

      <!-- MAIN GRID -->
      <div class="grid grid-cols-[280px_1fr] gap-4">

        <!-- SIDEBAR -->
        <aside class="sidebar space-y-4">

          <!-- game selector -->
          <div>
            <p class="sidebar-label">SELECT TARGET</p>
            <div class="game-list">
              <button
                v-for="g in games"
                :key="g.appid"
                @click="selectedGameId = g.appid"
                :class="['game-item', selectedGameId === g.appid && 'game-item--active']"
              >
                <span class="game-name truncate">{{ g.name }}</span>
                <span class="game-ccu">{{ fmtNum(g.current_ccu) }}</span>
              </button>
            </div>
          </div>

          <!-- game info -->
          <div v-if="selectedGame" class="info-panel">
            <p class="sidebar-label">TARGET INTEL</p>
            <div class="space-y-1.5 font-mono text-xs">
              <div class="info-row">
                <span class="info-key">APP ID</span>
                <span class="info-val">{{ selectedGame.appid }}</span>
              </div>
              <div class="info-row">
                <span class="info-key">ONLINE</span>
                <span class="info-val text-emerald-300">{{ fmtNum(selectedGame.current_ccu) }}</span>
              </div>
              <div class="info-row">
                <span class="info-key">APPROVAL</span>
                <span class="info-val">{{ selectedGame.positive_ratio ? (selectedGame.positive_ratio * 100).toFixed(1) + '%' : '--' }}</span>
              </div>
              <div v-if="selectedGame.price_usd != null" class="info-row">
                <span class="info-key">PRICE</span>
                <span class="info-val">${{ selectedGame.price_usd.toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <!-- what-if sliders -->
          <div class="info-panel">
            <p class="sidebar-label">SCENARIO PARAMS</p>
            <div class="space-y-4">
              <div>
                <div class="mb-1.5 flex justify-between font-mono text-[10px]">
                  <span class="text-emerald-700 uppercase tracking-wider">Discount Rate</span>
                  <span class="text-emerald-400">{{ discountRate }}%</span>
                </div>
                <input v-model.number="discountRate" type="range" min="0" max="100" step="1" class="terminal-range w-full" />
                <div class="mt-0.5 flex justify-between font-mono text-[9px] text-emerald-900">
                  <span>0%</span><span>100%</span>
                </div>
              </div>
              <div>
                <div class="mb-1.5 flex justify-between font-mono text-[10px]">
                  <span class="text-emerald-700 uppercase tracking-wider">Update Quality</span>
                  <span class="text-emerald-400">{{ updateQuality }}/10</span>
                </div>
                <input v-model.number="updateQuality" type="range" min="0" max="10" step="1" class="terminal-range w-full" />
                <div class="mt-0.5 flex justify-between font-mono text-[9px] text-emerald-900">
                  <span>0</span><span>10</span>
                </div>
              </div>
            </div>
          </div>

        </aside>

        <!-- CHART AREA -->
        <section class="chart-panel">
          <div v-if="loading" class="flex h-[500px] items-center justify-center font-mono text-sm text-emerald-700 tracking-widest">
            LOADING TELEMETRY...
          </div>
          <div v-else-if="errorMsg" class="flex h-[500px] items-center justify-center font-mono text-sm text-red-500">
            {{ errorMsg }}
          </div>
          <TrendChart
            v-else
            :title="selectedGame?.name || 'NO TARGET SELECTED'"
            :historical="trend"
            :predicted="predictPoints"
          />
        </section>

      </div>
    </div>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

:root {
  --bg: #030a06;
  --panel: #060f08;
  --border: rgba(16, 185, 129, 0.15);
  --green: #10b981;
  --green-dim: #064e35;
  --green-bright: #34d399;
}

* { box-sizing: border-box; }

body {
  background: var(--bg);
  color: #a7f3d0;
  font-family: 'Share Tech Mono', monospace;
  margin: 0;
}

.terminal-root {
  background:
    radial-gradient(ellipse at 20% 0%, rgba(16,185,129,0.06) 0%, transparent 60%),
    radial-gradient(ellipse at 80% 100%, rgba(16,185,129,0.04) 0%, transparent 50%),
    var(--bg);
  position: relative;
}

.scanlines {
  pointer-events: none;
  position: fixed;
  inset: 0;
  z-index: 100;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,0,0,0.08) 2px,
    rgba(0,0,0,0.08) 4px
  );
}

/* status dot */
.status-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 8px var(--green), 0 0 20px rgba(16,185,129,0.4);
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* sync button */
.sync-btn {
  background: transparent;
  border: 1px solid var(--green-dim);
  color: var(--green);
  padding: 6px 16px;
  cursor: pointer;
  transition: all 0.2s;
  clip-path: polygon(8px 0%, 100% 0%, calc(100% - 8px) 100%, 0% 100%);
}
.sync-btn:hover:not(:disabled) {
  background: rgba(16,185,129,0.1);
  border-color: var(--green);
  box-shadow: 0 0 12px rgba(16,185,129,0.2);
}
.sync-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.sync-icon { display: inline-block; margin-right: 6px; }
.sync-btn:not(:disabled):hover .sync-icon { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* stat cards */
.stat-card {
  background: var(--panel);
  border: 1px solid var(--border);
  padding: 16px 20px;
  position: relative;
  overflow: hidden;
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--green), transparent);
  opacity: 0.5;
}
.card-label {
  font-family: 'Share Tech Mono', monospace;
  font-size: 9px;
  letter-spacing: 0.2em;
  color: #065f46;
  margin-bottom: 8px;
}
.card-value {
  font-family: 'Rajdhani', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  color: #ecfdf5;
  line-height: 1;
  margin-bottom: 4px;
}
.card-sub {
  font-size: 10px;
  color: #064e35;
  letter-spacing: 0.05em;
}

/* sidebar */
.sidebar {
  background: var(--panel);
  border: 1px solid var(--border);
  padding: 16px;
}
.sidebar-label {
  font-size: 9px;
  letter-spacing: 0.2em;
  color: #065f46;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 6px;
}

/* game list */
.game-list {
  max-height: 240px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--green-dim) transparent;
}
.game-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 6px 8px;
  background: transparent;
  border: none;
  border-left: 2px solid transparent;
  color: #6ee7b7;
  font-family: 'Share Tech Mono', monospace;
  font-size: 11px;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
  gap: 8px;
}
.game-item:hover { background: rgba(16,185,129,0.05); color: #a7f3d0; }
.game-item--active {
  border-left-color: var(--green);
  background: rgba(16,185,129,0.08);
  color: var(--green-bright);
}
.game-name { flex: 1; min-width: 0; }
.game-ccu { font-size: 10px; color: #065f46; white-space: nowrap; }
.game-item--active .game-ccu { color: var(--green); }

/* info panel */
.info-panel {
  background: rgba(0,0,0,0.3);
  border: 1px solid var(--border);
  padding: 12px;
}
.info-row {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
  border-bottom: 1px solid rgba(16,185,129,0.05);
}
.info-key { color: #065f46; letter-spacing: 0.1em; }
.info-val { color: #6ee7b7; }

/* range slider */
.terminal-range {
  -webkit-appearance: none;
  appearance: none;
  height: 2px;
  background: var(--green-dim);
  outline: none;
}
.terminal-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px; height: 12px;
  background: var(--green);
  clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
  cursor: pointer;
}

/* chart panel */
.chart-panel {
  background: var(--panel);
  border: 1px solid var(--border);
  padding: 16px;
  position: relative;
}
.chart-panel::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--green), transparent);
  opacity: 0.3;
}
</style>
