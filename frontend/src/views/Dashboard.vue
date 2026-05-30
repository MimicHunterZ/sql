<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getGames, getOverview } from '../api'

const router   = useRouter()
const loading  = ref(true)
const errorMsg = ref('')
const games    = ref([])
const overview = ref({ monitored_games: 0, warning: 'normal' })

function fmtNum(n) {
  if (n == null) return '--'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + 'M'
  if (n >= 1_000)     return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}
function warningText(w) {
  if (w === 'high_peak_risk') return '峰值预警'
  if (w === 'attention')      return '需要注意'
  return '正常'
}
function warningColor(w) {
  if (w === 'high_peak_risk') return '#f472b6'
  if (w === 'attention')      return '#facc15'
  return '#60a5fa'
}

onMounted(async () => {
  try {
    const [ov, gm] = await Promise.all([getOverview(), getGames()])
    overview.value = ov
    games.value    = gm
  } catch (e) {
    errorMsg.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="dashboard">

    <!-- page title -->
    <div class="page-header">
      <div class="flex items-center gap-3">
        <div class="status-dot"></div>
        <div>
          <h1 class="page-title">Steam CCU Intelligence</h1>
          <p class="page-sub">实时监控 · 同时在线用户数 · 趋势预测分析</p>
        </div>
      </div>
    </div>

    <!-- stat cards -->
    <section class="stat-grid">
      <div class="glass-card stat-card">
        <p class="card-label">监控游戏</p>
        <p class="card-value">{{ overview.monitored_games || 0 }}</p>
        <p class="card-sub">活跃数据源</p>
      </div>
      <div class="glass-card stat-card">
        <p class="card-label">峰值游戏</p>
        <p class="card-value truncate text-2xl" style="font-size:1.3rem">
          {{ overview.top_game_name || '--' }}
        </p>
        <p class="card-sub">{{ fmtNum(overview.top_game_ccu) }} 人同时在线</p>
      </div>
      <div class="glass-card stat-card">
        <p class="card-label">系统状态</p>
        <p class="card-value text-2xl" :style="{ color: warningColor(overview.warning), WebkitTextFillColor: warningColor(overview.warning) }">
          {{ warningText(overview.warning) }}
        </p>
        <p class="card-sub">预测置信度：高</p>
      </div>
    </section>

    <!-- game ranking table -->
    <div class="glass-card ranking-card">
      <p class="section-label">游戏排行榜</p>

      <div v-if="loading" class="loading-msg">加载中...</div>
      <div v-else-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

      <div v-else class="game-table">
        <!-- header -->
        <div class="table-head">
          <span class="col-rank">#</span>
          <span class="col-cover"></span>
          <span class="col-name">游戏名称</span>
          <span class="col-ccu">当前 CCU</span>
          <span class="col-tags">标签</span>
          <span class="col-price">价格</span>
          <span class="col-action"></span>
        </div>
        <!-- rows -->
        <div
          v-for="(g, i) in games"
          :key="g.appid"
          class="table-row"
          @click="router.push(`/game/${g.appid}`)"
        >
          <span class="col-rank">
            <span class="rank-num" :class="i < 3 && `rank-top${i+1}`">{{ i + 1 }}</span>
          </span>
          <span class="col-cover">
            <img
              :src="`https://cdn.akamai.steamstatic.com/steam/apps/${g.appid}/capsule_sm_120.jpg`"
              :alt="g.name"
              class="game-cover"
              loading="lazy"
            />
          </span>
          <span class="col-name">{{ g.name }}</span>
          <span class="col-ccu ccu-val">{{ fmtNum(g.current_ccu) }}</span>
          <span class="col-tags">
            <span v-for="tag in (g.tags || []).slice(0,2)" :key="tag" class="tag-badge">{{ tag }}</span>
          </span>
          <span class="col-price">
            <span v-if="g.price_usd === 0 || g.price_usd == null" class="price-free">免费</span>
            <span v-else class="price-paid">${{ g.price_usd?.toFixed(2) }}</span>
          </span>
          <span class="col-action">
            <span class="detail-arrow">→</span>
          </span>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 20px; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.ranking-card { padding: 24px; }

.loading-msg { text-align: center; color: #6b7280; padding: 40px; font-size: 13px; }
.error-msg   { text-align: center; color: #f87171; padding: 40px; font-size: 13px; }

/* table */
.game-table { display: flex; flex-direction: column; gap: 0; }

.table-head, .table-row {
  display: grid;
  grid-template-columns: 40px 72px 1fr 120px 180px 80px 32px;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 12px;
}
.table-head {
  color: #6b7280;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: .12em;
  text-transform: uppercase;
  border-bottom: 1px solid var(--border);
  margin-bottom: 4px;
}
.table-row {
  color: #d1d5db;
  border-radius: 10px;
  cursor: pointer;
  transition: background .15s, transform .15s;
}
.table-row:hover {
  background: rgba(96,165,250,.07);
  transform: translateX(4px);
}
.table-row:hover .detail-arrow { opacity: 1; color: var(--blue); }

.rank-num { font-family: 'Rajdhani', sans-serif; font-weight: 700; font-size: 14px; color: #4b5563; }
.rank-top1 { color: #facc15; text-shadow: 0 0 10px rgba(250,204,21,.5); }
.rank-top2 { color: #94a3b8; }
.rank-top3 { color: #cd7c2f; }

.col-name { display: flex; align-items: center; gap: 8px; font-weight: 500; overflow: hidden; white-space: nowrap; }
.col-cover { display: flex; align-items: center; }
.game-cover {
  width: 68px;
  height: 32px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid rgba(255,255,255,.08);
  display: block;
}
.ccu-val { font-family: 'Rajdhani', sans-serif; font-size: 15px; font-weight: 700; color: var(--cyan); }

.tag-badge {
  display: inline-block;
  padding: 2px 7px;
  background: rgba(96,165,250,.1);
  border: 1px solid rgba(96,165,250,.2);
  border-radius: 999px;
  font-size: 10px;
  color: #93c5fd;
  margin-right: 4px;
}
.price-free { color: #4ade80; font-weight:600; font-size:11px; }
.price-paid { color: #9ca3af; font-size:12px; }
.detail-arrow { opacity: 0; transition: opacity .15s; font-size: 14px; }
</style>
