<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  GridComponent, LegendComponent, TooltipComponent,
  MarkLineComponent, DataZoomComponent,
} from 'echarts/components'
import TrendChart from '../components/TrendChart.vue'
import { getGameDetail, getHistory, getPredict, getPredictMonthly, getPrice, getTrend } from '../api'

use([CanvasRenderer, LineChart, GridComponent, LegendComponent,
     TooltipComponent, MarkLineComponent, DataZoomComponent])

const route  = useRoute()
const router = useRouter()

const gameId         = computed(() => route.params.id)
const loading        = ref(true)
const detail         = ref(null)
const trend          = ref([])
const predictPts     = ref([])
const monthlyPreds   = ref([])
const history        = ref([])
const priceData      = ref(null)   // CNY price history
const discountRate   = ref(20)
const updateQuality  = ref(6)

let debounce = null

function fmtNum(n) {
  if (n == null) return '--'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + 'M'
  if (n >= 1_000)     return (n / 1_000).toFixed(1) + 'K'
  return Number(n).toLocaleString()
}

async function loadPredict() {
  try {
    const [r7, rm] = await Promise.allSettled([
      getPredict(Number(gameId.value), discountRate.value, updateQuality.value),
      getPredictMonthly(gameId.value, discountRate.value, updateQuality.value),
    ])
    predictPts.value   = r7.status === 'fulfilled' ? r7.value.points       : []
    monthlyPreds.value = rm.status === 'fulfilled' ? rm.value.predictions  : []
  } catch { predictPts.value = []; monthlyPreds.value = [] }
}

function debouncedPredict() {
  clearTimeout(debounce)
  debounce = setTimeout(loadPredict, 400)
}

async function load() {
  loading.value = true
  try {
    const [trendResp, histResp] = await Promise.allSettled([
      getTrend(gameId.value, 30),
      getHistory(gameId.value),
    ])
    trend.value   = trendResp.status === 'fulfilled' ? trendResp.value.points  : []
    history.value = histResp.status  === 'fulfilled' ? histResp.value.history  : []

    try { const det = await getGameDetail(gameId.value); detail.value = det }
    catch { detail.value = null }

    try { priceData.value = await getPrice(gameId.value) }
    catch { priceData.value = null }

    await loadPredict()
  } finally {
    loading.value = false
  }
}

watch(gameId, load)
watch([discountRate, updateQuality], debouncedPredict)
onMounted(load)

// ── CNY Price history chart ────────────────────────────────────────────────────
const priceOption = computed(() => {
  const pd = priceData.value
  if (!pd || pd.is_free) return null

  const hist = pd.history || []
  if (hist.length < 2) return null

  // Build step-chart data: each segment repeats the price until next change
  const dates  = hist.map(h => h.date)
  const prices = hist.map(h => h.price_cny)
  const atl    = pd.all_time_low_cny

  // Mark lowest-price points
  const markPoints = hist
    .filter(h => h.price_cny === atl && atl < pd.initial_cny)
    .map(h => ({ coord: [h.date, h.price_cny], value: `¥${atl}` }))

  return {
    backgroundColor: 'transparent',
    grid: { top: 36, bottom: 56, left: 64, right: 24 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(17,24,39,.95)',
      borderColor: 'rgba(96,165,250,.3)',
      textStyle: { color: '#e0e0e0', fontSize: 12 },
      formatter(params) {
        const p = params[0]
        const entry = hist.find(h => h.date === p.axisValueLabel)
        const label = entry?.label ? `<div style="color:#fbbf24;font-size:10px">${entry.label}</div>` : ''
        const disc  = entry?.discount_pct > 0 ? `<span style="color:#4ade80;margin-left:6px">-${entry.discount_pct}%</span>` : ''
        return `<div style="font-size:11px">
          <b style="color:#93c5fd">${p.axisValueLabel}</b>${label}
          <div>价格 <b style="color:#34d399">¥${Number(p.value).toFixed(2)}</b>${disc}</div>
        </div>`
      },
    },
    xAxis: {
      type: 'category', data: dates,
      axisLabel: { color: '#6b7280', fontSize: 9, rotate: 20 },
      axisLine:  { lineStyle: { color: 'rgba(96,165,250,.2)' } },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      min: v => Math.floor(v.min * 0.8),
      axisLabel: {
        color: '#6b7280', fontSize: 10,
        formatter: v => `¥${v}`,
      },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,.05)' } },
    },
    series: [{
      name: 'CNY 价格',
      type: 'line',
      step: 'end',          // step chart — prices don't interpolate
      data: prices,
      symbol: 'circle',
      symbolSize: v => v === atl && atl < pd.initial_cny ? 8 : 0,
      lineStyle:  { color: '#e2e8f0', width: 2 },
      itemStyle:  { color: '#4ade80' },
      areaStyle: {
        color: { type:'linear', x:0,y:0,x2:0,y2:1,
          colorStops:[{offset:0,color:'rgba(226,232,240,.15)'},{offset:1,color:'rgba(226,232,240,.02)'}] },
      },
      markLine: atl < pd.initial_cny ? {
        silent: true, symbol: 'none',
        lineStyle: { color: 'rgba(74,222,128,.5)', type: 'dashed', width: 1 },
        data: [{ yAxis: atl, name: '史低',
                 label: { formatter: `史低 ¥${atl}`, color: '#4ade80', fontSize: 10, position: 'insideStartTop' } }],
      } : undefined,
    }],
  }
})
const historyOption = computed(() => {
  const rows = [...(history.value || [])].reverse()   // oldest → newest
  const preds = monthlyPreds.value || []

  // Build combined x-axis labels
  const histLabels = rows.map(r => r.month)
  const predLabels = preds.map(r => r.month)
  const allLabels  = [...histLabels, ...predLabels]

  // Historical series (avg + peak)
  const histAvg  = rows.map(r => r.avg_players)
  const histPeak = rows.map(r => r.peak_players)

  // Predicted avg: pad nulls for historical portion, then values
  const predAvgSeries = [
    ...rows.map((_, i) => (i === rows.length - 1 ? rows[rows.length - 1].avg_players : null)),
    ...preds.map(r => r.avg_players),
  ]

  return {
    backgroundColor: 'transparent',
    grid: { top: 40, bottom: 60, left: 56, right: 24, containLabel: false },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(17,24,39,.95)',
      borderColor: 'rgba(96,165,250,.3)',
      textStyle: { color: '#e0e0e0', fontSize: 12 },
      formatter(params) {
        const m = params[0]?.axisValueLabel || ''
        const lines = params
          .filter(p => p.value != null)
          .map(p =>
            `<div style="display:flex;justify-content:space-between;gap:16px">
              <span style="color:${p.color}">${p.seriesName}</span>
              <b>${Number(p.value).toLocaleString()}</b>
             </div>`
          ).join('')
        return `<div style="font-size:11px"><b style="color:#93c5fd">${m}</b><br>${lines}</div>`
      },
    },
    legend: {
      top: 6, right: 0, textStyle: { color: '#9ca3af', fontSize: 11 },
      itemWidth: 16, itemHeight: 3,
    },
    dataZoom: [{ type: 'inside', start: 60, end: 100 }],
    xAxis: {
      type: 'category',
      data: allLabels,
      axisLabel: { color: '#6b7280', fontSize: 10, rotate: 30 },
      axisLine:  { lineStyle: { color: 'rgba(96,165,250,.2)' } },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#6b7280', fontSize: 10,
        formatter: v => v >= 1e6 ? (v/1e6).toFixed(1)+'M' : v >= 1e3 ? (v/1e3).toFixed(0)+'K' : v,
      },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,.06)' } },
    },
    series: [
      {
        name: '月均 CCU',
        type: 'line',
        data: [...histAvg, ...preds.map(() => null)],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#60a5fa', width: 2 },
        areaStyle: { color: { type:'linear', x:0,y:0,x2:0,y2:1, colorStops:[{offset:0,color:'rgba(96,165,250,.35)'},{offset:1,color:'rgba(96,165,250,.02)'}] } },
      },
      {
        name: '月峰值',
        type: 'line',
        data: [...histPeak, ...preds.map(() => null)],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#a78bfa', width: 1.5, type: 'dashed' },
      },
      ...(preds.length ? [{
        name: '预测均值',
        type: 'line',
        data: predAvgSeries,
        smooth: true,
        symbol: 'none',
        connectNulls: true,
        lineStyle: { color: '#fbbf24', width: 2, type: 'dashed' },
        areaStyle: { color: { type:'linear', x:0,y:0,x2:0,y2:1, colorStops:[{offset:0,color:'rgba(251,191,36,.25)'},{offset:1,color:'rgba(251,191,36,.02)'}] } },
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { color: 'rgba(251,191,36,.5)', type: 'solid', width: 1 },
          data: [{ xAxis: histLabels[histLabels.length - 1], name: '预测起点',
                   label: { formatter: '预测→', color: '#fbbf24', fontSize: 9, position: 'insideEndTop' } }],
        },
      }] : []),
    ],
  }
})
</script>

<template>
  <div class="game-detail">

    <!-- back + title -->
    <div
      class="page-header"
      :style="detail ? {
        backgroundImage: `linear-gradient(to right, rgba(10,10,26,.95) 40%, rgba(10,10,26,.6)),
                          url(https://cdn.akamai.steamstatic.com/steam/apps/${gameId}/capsule_616x353.jpg)`,
      } : {}"
    >
      <button class="btn-back" @click="router.push('/')">← 返回</button>
      <div class="header-info" v-if="detail">
        <div class="header-cover-wrap">
          <img
            :src="`https://cdn.akamai.steamstatic.com/steam/apps/${gameId}/header.jpg`"
            :alt="detail.name"
            class="header-cover"
          />
        </div>
        <div>
          <h1 class="page-title">{{ detail.name }}</h1>
          <p class="page-sub">
            App {{ gameId }} ·
            {{ detail.developer }} ·
            {{ detail.release_date }} ·
            <span :class="detail.is_free ? 'text-green-400' : 'text-gray-400'">
              {{ detail.is_free ? '免费' : '付费' }}
            </span>
          </p>
        </div>
      </div>
      <div v-else>
        <h1 class="page-title">游戏详情</h1>
        <p class="page-sub">App {{ gameId }}</p>
      </div>
    </div>

    <div v-if="loading" class="loading-block">加载数据中...</div>
    <template v-else>

      <!-- top info strip -->
      <div v-if="detail" class="info-strip">
        <div class="info-chip">
          <span class="info-chip-key">评价</span>
          <span class="info-chip-val">{{ detail.review_summary || '--' }}</span>
        </div>
        <div class="info-chip" v-for="tag in (detail.tags || []).slice(0,5)" :key="tag">
          <span class="info-chip-val tag">{{ tag }}</span>
        </div>
      </div>

      <!-- two-column: charts left, predict right -->
      <div class="content-grid">

        <!-- left column: charts -->
        <div class="charts-col">

          <!-- 近期 CCU 趋势 + 7 天预测 -->
          <div class="glass-card chart-wrap">
            <p class="section-label">近期 CCU 趋势（30 天）</p>
            <TrendChart
              :title="detail?.name || ''"
              :historical="trend"
              :predicted="predictPts"
            />
          </div>

          <!-- 月度历史 -->
          <div class="glass-card chart-wrap">
            <p class="section-label">历史月度 CCU（SteamCharts 数据）</p>
            <div v-if="!history.length" class="no-data">暂无历史数据</div>
            <VChart v-else :option="historyOption" :autoresize="true" style="height:280px" />
          </div>

          <!-- CNY 价格走势 -->
          <div class="glass-card chart-wrap" v-if="priceData && !priceData.is_free">
            <div class="price-chart-header">
              <p class="section-label" style="margin:0;border:none;padding:0">CNY 价格走势</p>
              <div class="price-stats">
                <div class="pstat">
                  <span class="pstat-lbl">原价</span>
                  <span class="pstat-val">¥{{ priceData.initial_cny }}</span>
                </div>
                <div class="pstat">
                  <span class="pstat-lbl">史低</span>
                  <span class="pstat-val pstat-green">¥{{ priceData.all_time_low_cny }}</span>
                </div>
                <div class="pstat">
                  <span class="pstat-lbl">一年内史低</span>
                  <span class="pstat-val pstat-green">{{ priceData.all_time_low_count_1y }} 次</span>
                </div>
              </div>
            </div>
            <VChart :option="priceOption" :autoresize="true" style="height:220px;margin-top:12px" />
          </div>
          <div class="glass-card chart-wrap" v-else-if="priceData && priceData.is_free">
            <p class="section-label">CNY 价格走势</p>
            <div class="no-data" style="color:#4ade80">🎮 免费游戏，无需付费</div>
          </div>

        </div>

          <!-- right column: predict params -->
        <div class="predict-col">
          <div class="glass-card predict-card">
            <p class="section-label">预测参数 What-If</p>

            <div class="slider-group">
              <div class="slider-row">
                <span class="slider-label">折扣率</span>
                <span class="slider-val">{{ discountRate }}%</span>
              </div>
              <input v-model.number="discountRate" type="range" min="0" max="100" class="terminal-range" />
            </div>

            <div class="slider-group">
              <div class="slider-row">
                <span class="slider-label">更新质量</span>
                <span class="slider-val">{{ updateQuality }} / 10</span>
              </div>
              <input v-model.number="updateQuality" type="range" min="0" max="10" class="terminal-range" />
            </div>

            <div class="predict-results">
              <p class="section-label" style="margin-top:16px">月度预测（2026）</p>
              <div v-if="monthlyPreds.length" class="predict-list">
                <div v-for="p in monthlyPreds" :key="p.month" class="predict-row">
                  <span class="predict-month">{{ p.month }}</span>
                  <span class="predict-ccu">{{ fmtNum(p.avg_players) }}</span>
                </div>
              </div>
              <div v-else class="no-data">暂无预测数据</div>
            </div>
          </div>
        </div>

      </div>
    </template>
  </div>
</template>

<style scoped>
.game-detail { display: flex; flex-direction: column; gap: 18px; }

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 14px;
  background-color: rgba(17,24,39,.85);
  background-size: cover;
  background-position: center right;
  border: 1px solid var(--border);
  min-height: 90px;
}
.btn-back {
  background: transparent;
  border: 1px solid var(--border);
  color: #9ca3af;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  transition: all .2s;
  white-space: nowrap;
  flex-shrink: 0;
}
.btn-back:hover { border-color: var(--blue); color: var(--blue); }

.header-info { display: flex; align-items: center; gap: 16px; }
.header-cover-wrap {
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,.12);
  box-shadow: 0 4px 20px rgba(0,0,0,.5);
}
.header-cover {
  display: block;
  width: 184px;
  height: 86px;
  object-fit: cover;
}

.loading-block { text-align:center; padding: 80px; color: #6b7280; font-size:13px; }

.info-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.info-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(96,165,250,.08);
  border: 1px solid rgba(96,165,250,.2);
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 11px;
}
.info-chip-key { color: #6b7280; }
.info-chip-val { color: #93c5fd; font-weight: 600; }
.info-chip-val.tag { color: #c4b5fd; }

.content-grid {
  display: grid;
  grid-template-columns: 1fr 260px;
  gap: 16px;
  align-items: start;
}

.charts-col { display: flex; flex-direction: column; gap: 16px; }

.chart-wrap { padding: 20px; }
.no-data { text-align:center; padding:40px; color:#6b7280; font-size:12px; }

.price-chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}
.price-stats { display: flex; gap: 20px; align-items: center; }
.pstat { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.pstat-lbl { font-size: 10px; color: #6b7280; }
.pstat-val { font-family: 'Rajdhani', sans-serif; font-size: 16px; font-weight: 700; color: #e2e8f0; }
.pstat-green { color: #4ade80; }

.predict-col {}
.predict-card { padding: 20px; }

.slider-group { margin-bottom: 16px; }
.slider-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.slider-label { font-size:11px; color:#9ca3af; text-transform:uppercase; letter-spacing:.08em; }
.slider-val   { font-size:11px; color: var(--blue); font-weight:600; }

.predict-results { display: flex; flex-direction: column; gap: 4px; }
.predict-list { display: flex; flex-direction: column; gap: 3px; max-height: 320px; overflow-y: auto; }
.predict-row {
  display: flex;
  justify-content: space-between;
  padding: 5px 8px;
  border-radius: 8px;
  background: rgba(0,0,0,.2);
  font-size: 12px;
}
.predict-month { color: #9ca3af; font-size: 11px; }
.predict-ccu  { color: #fbbf24; font-weight: 600; font-family:'Rajdhani',sans-serif; font-size:14px; }
</style>
