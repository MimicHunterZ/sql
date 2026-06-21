<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
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
import { gameImage } from '../storefront'

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
const reviewsCardEl  = ref(null)
const aboutCardHeight = ref(null)

let debounce = null
let reviewResizeObserver = null

function fmtNum(n) {
  if (n == null) return '--'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + 'M'
  if (n >= 1_000)     return (n / 1_000).toFixed(1) + 'K'
  return Number(n).toLocaleString()
}
function fmtPercent(n) {
  if (n == null) return '--'
  return `${Number(n).toFixed(1)}%`
}
function reviewTone(votedUp) {
  return votedUp ? '推荐' : '不推荐'
}
function fmtCny(n) {
  if (n == null) return '--'
  return `¥${Number(n).toFixed(2).replace(/\.00$/, '')}`
}

const priceLabel = computed(() => {
  const pd = priceData.value
  if (detail.value?.is_free || pd?.is_free) return '免费开玩'
  if (pd?.current_cny != null) return fmtCny(pd.current_cny)
  return '价格暂缺'
})
const priceNote = computed(() => {
  const pd = priceData.value
  if (!pd || pd.is_free) return 'Steam 免费游戏'
  if (pd.current_discount > 0) return `当前 -${pd.current_discount}% · 原价 ${fmtCny(pd.initial_cny)}`
  if (pd.all_time_low_cny != null && pd.all_time_low_cny < pd.current_cny) {
    return `史低 ${fmtCny(pd.all_time_low_cny)}`
  }
  return '当前 CNY 价格'
})
const aboutText = computed(() => detail.value?.detailed_desc || detail.value?.short_desc || '')

function syncAboutCardHeight() {
  if (typeof window === 'undefined') return

  if (window.matchMedia('(max-width: 980px)').matches) {
    aboutCardHeight.value = null
    return
  }

  const el = reviewsCardEl.value
  aboutCardHeight.value = el ? Math.ceil(el.getBoundingClientRect().height) : null
}

async function bindReviewCardHeight() {
  await nextTick()

  reviewResizeObserver?.disconnect()
  reviewResizeObserver = null

  const el = reviewsCardEl.value
  if (!el || typeof ResizeObserver === 'undefined') {
    syncAboutCardHeight()
    return
  }

  reviewResizeObserver = new ResizeObserver(syncAboutCardHeight)
  reviewResizeObserver.observe(el)
  syncAboutCardHeight()
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
watch([detail, loading], bindReviewCardHeight)
onMounted(() => {
  load()
  window.addEventListener('resize', syncAboutCardHeight)
})
onBeforeUnmount(() => {
  clearTimeout(debounce)
  reviewResizeObserver?.disconnect()
  window.removeEventListener('resize', syncAboutCardHeight)
})

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

    <section
      class="store-detail-hero"
      :style="{
        backgroundImage: `linear-gradient(90deg, rgba(9,14,22,.98) 0%, rgba(9,14,22,.82) 44%, rgba(9,14,22,.3) 100%), url(${gameImage(gameId, 'hero')})`,
      }"
    >
      <div class="detail-toolbar">
        <button class="btn-back" @click="router.push('/')">← 商店</button>
        <button class="btn-back" @click="router.push('/dashboard')">数据总览</button>
      </div>

      <div class="detail-hero-grid" v-if="detail">
        <div class="detail-media">
          <img :src="gameImage(gameId, 'header')" :alt="detail.name" class="detail-header-img" />
          <div class="detail-screens">
            <img :src="gameImage(gameId, 'small')" :alt="detail.name" />
            <img :src="gameImage(gameId, 'hero')" :alt="detail.name" />
          </div>
        </div>

        <div class="detail-copy">
          <p class="store-kicker">STEAM GAME PAGE</p>
          <h1>{{ detail.name }}</h1>
          <p class="detail-desc">
            {{ detail.short_desc || '这款游戏正在被纳入 CCU Intelligence 监控，当前页面汇总商店信息、在线人数、价格历史和趋势预测。' }}
          </p>

          <div class="detail-meta">
            <div>
              <span>最近评价</span>
              <b>{{ detail.review_summary || '--' }}</b>
            </div>
            <div>
              <span>好评率</span>
              <b>{{ fmtPercent(detail.positive_ratio) }}</b>
            </div>
            <div>
              <span>总评测</span>
              <b>{{ fmtNum(detail.total_reviews) }}</b>
            </div>
          </div>

          <div class="detail-meta detail-meta--secondary">
            <div>
              <span>开发商</span>
              <b>{{ detail.developer || '--' }}</b>
            </div>
            <div>
              <span>发行商</span>
              <b>{{ detail.publisher || '--' }}</b>
            </div>
            <div>
              <span>发行日期</span>
              <b>{{ detail.release_date || '--' }}</b>
            </div>
          </div>

          <div class="detail-tags">
            <span v-for="tag in (detail.tags || []).slice(0, 8)" :key="tag">{{ tag }}</span>
          </div>

          <div class="detail-buy">
            <span class="buy-label">当前价格</span>
            <strong>{{ priceLabel }}</strong>
            <em>{{ priceNote }}</em>
          </div>
        </div>
      </div>

      <div class="detail-hero-grid" v-else>
        <div class="detail-copy">
          <p class="store-kicker">APP {{ gameId }}</p>
          <h1>游戏详情</h1>
          <p class="detail-desc">商店详情暂未加载，数据图表仍可继续查看。</p>
        </div>
      </div>
    </section>

    <div v-if="loading" class="loading-block">加载数据中...</div>
    <template v-else>

      <section v-if="detail" class="store-data-strip">
        <div class="strip-card">
          <span>当前 CCU</span>
          <b>{{ fmtNum(detail.current_ccu) }}</b>
        </div>
        <div class="strip-card">
          <span>历史峰值</span>
          <b>{{ fmtNum(detail.peak_ccu_alltime) }}</b>
        </div>
        <div class="strip-card">
          <span>类型</span>
          <b>{{ detail.genre || (detail.tags || [])[0] || '--' }}</b>
        </div>
        <div class="strip-card">
          <span>AppID</span>
          <b>{{ gameId }}</b>
        </div>
      </section>

      <section v-if="detail" class="store-info-grid">
        <div class="glass-card about-card" :style="aboutCardHeight ? { height: `${aboutCardHeight}px` } : null">
          <p class="section-label">游戏介绍</p>
          <p class="about-note" :title="aboutText">{{ aboutText }}</p>
        </div>

        <div class="glass-card reviews-card" ref="reviewsCardEl">
          <p class="section-label">玩家评价与热评</p>
          <div class="review-summary">
            <div>
              <span>评价摘要</span>
              <b>{{ detail.review_summary || '--' }}</b>
            </div>
            <div>
              <span>好评</span>
              <b>{{ fmtNum(detail.total_positive) }}</b>
            </div>
            <div>
              <span>好评率</span>
              <b>{{ fmtPercent(detail.positive_ratio) }}</b>
            </div>
          </div>

          <div v-if="(detail.hot_reviews || []).length" class="hot-review-list">
            <article
              v-for="(review, index) in (detail.hot_reviews || []).slice(0, 3)"
              :key="index"
              class="hot-review"
              :class="{ 'hot-review--down': !review.voted_up }"
            >
              <header>
                <span>{{ reviewTone(review.voted_up) }}</span>
                <em>{{ fmtNum(review.votes_up) }} 人觉得有价值</em>
              </header>
              <p>{{ review.review }}</p>
              <small>{{ review.playtime_hours || 0 }} 小时游玩</small>
            </article>
          </div>
          <div v-else class="no-data">暂无热评数据</div>
        </div>
      </section>

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
            <div class="no-data" style="color:#4ade80">免费游戏，无需付费</div>
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
.game-detail {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 1360px;
  margin: 0 auto;
}

.store-detail-hero {
  position: relative;
  min-height: 430px;
  padding: 20px;
  background-size: cover;
  background-position: center;
  border: 1px solid rgba(103,193,245,.2);
  box-shadow: 0 28px 90px rgba(0,0,0,.34);
  overflow: hidden;
}

.store-detail-hero::after {
  content: '';
  position: absolute;
  inset: auto 0 0;
  height: 3px;
  background: linear-gradient(90deg, #67c1f5, #a4d007, #f5c451);
}

.detail-toolbar {
  position: relative;
  z-index: 2;
  display: flex;
  gap: 8px;
  margin-bottom: 34px;
}

.btn-back {
  background: rgba(8,13,20,.62);
  border: 1px solid rgba(103,193,245,.24);
  color: #c7d5e0;
  padding: 8px 14px;
  font-size: 12px;
  cursor: pointer;
  transition: all .2s;
  white-space: nowrap;
  flex-shrink: 0;
}
.btn-back:hover { border-color: #67c1f5; color: #67c1f5; background: rgba(103,193,245,.1); }

.detail-hero-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(280px, 460px) minmax(0, 1fr);
  gap: 28px;
  align-items: end;
}

.detail-media {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.detail-header-img {
  width: 100%;
  aspect-ratio: 460 / 215;
  object-fit: cover;
  box-shadow: 0 18px 50px rgba(0,0,0,.42);
}

.detail-screens {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 10px;
}

.detail-screens img {
  width: 100%;
  height: 74px;
  object-fit: cover;
  opacity: .82;
}

.detail-copy {
  max-width: 760px;
  padding-bottom: 4px;
}

.store-kicker {
  color: #67c1f5;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .12em;
  text-transform: uppercase;
}

.detail-copy h1 {
  font-family: 'Barlow Condensed', 'Noto Sans SC', sans-serif;
  color: #fff;
  font-size: clamp(3rem, 6vw, 6.5rem);
  line-height: .88;
  margin: 8px 0 16px;
  letter-spacing: 0;
  text-shadow: 0 10px 40px rgba(0,0,0,.55);
}

.detail-desc {
  color: #c7d5e0;
  max-width: 680px;
  font-size: 15px;
  line-height: 1.7;
  margin-bottom: 18px;
}

.detail-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.detail-meta--secondary {
  margin-top: -4px;
}

.detail-meta div,
.strip-card {
  min-width: 0;
  background: rgba(8, 13, 20, .55);
  border: 1px solid rgba(255,255,255,.08);
  padding: 10px 12px;
}

.detail-meta span,
.strip-card span {
  display: block;
  color: #8f98a0;
  font-size: 11px;
  margin-bottom: 5px;
}

.detail-meta b,
.strip-card b {
  display: block;
  color: #eaf6ff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-bottom: 18px;
}

.detail-tags span {
  color: #67c1f5;
  background: rgba(103,193,245,.12);
  border: 1px solid rgba(103,193,245,.18);
  padding: 5px 9px;
  font-size: 12px;
}

.detail-buy {
  display: grid;
  grid-template-columns: auto auto 1fr;
  align-items: center;
  width: min(430px, 100%);
  background: rgba(0,0,0,.42);
  border: 1px solid rgba(255,255,255,.1);
  padding: 10px 12px;
  column-gap: 12px;
}

.detail-buy .buy-label {
  color: #8f98a0;
  font-size: 12px;
  font-weight: 800;
}

.detail-buy strong {
  color: #b7e433;
  font-family: 'Barlow Condensed', 'Noto Sans SC', sans-serif;
  font-size: 1.6rem;
  line-height: 1;
  font-weight: 800;
}

.detail-buy em {
  color: #c7d5e0;
  justify-self: end;
  font-size: 12px;
  font-style: normal;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.loading-block { text-align:center; padding: 80px; color: #6b7280; font-size:13px; }

.store-data-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.strip-card {
  background: rgba(20, 43, 66, .7);
  border-color: rgba(103,193,245,.18);
}

.strip-card b {
  font-family: 'Barlow Condensed', 'Noto Sans SC', sans-serif;
  font-size: 1.6rem;
  color: #f3f7fb;
}

.store-info-grid {
  display: grid;
  grid-template-columns: minmax(360px, .86fr) minmax(0, 1.14fr);
  gap: 16px;
  align-items: stretch;
}

.about-card,
.reviews-card {
  padding: 20px;
}

.about-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.about-note {
  color: #c7d5e0;
  display: block;
  flex: 1 1 0;
  font-family: 'Noto Sans SC', serif;
  font-size: 15px;
  font-weight: 500;
  letter-spacing: .02em;
  line-height: 1.9;
  margin-bottom: 0;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  text-shadow: 0 1px 0 rgba(0,0,0,.24);
}

.reviews-card {
  display: flex;
  flex-direction: column;
}

.review-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.review-summary div {
  min-width: 0;
  background: rgba(8,13,20,.42);
  border: 1px solid rgba(255,255,255,.08);
  padding: 9px 10px;
}

.review-summary span {
  display: block;
  color: #8f98a0;
  font-size: 11px;
  margin-bottom: 4px;
}

.review-summary b {
  display: block;
  color: #b7e433;
  font-family: 'Barlow Condensed', 'Noto Sans SC', sans-serif;
  font-size: 1.45rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-review-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hot-review {
  background: rgba(8,13,20,.36);
  border: 1px solid rgba(183,228,51,.16);
  border-left: 3px solid #b7e433;
  min-height: 92px;
  padding: 12px 14px;
}

.hot-review--down {
  border-color: rgba(248,113,113,.16);
  border-left-color: #f87171;
}

.hot-review header {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.hot-review header span {
  color: #eaf6ff;
  font-size: 12px;
  font-weight: 800;
}

.hot-review header em,
.hot-review small {
  color: #8f98a0;
  font-style: normal;
  font-size: 11px;
}

.hot-review p {
  color: #c7d5e0;
  display: -webkit-box;
  font-size: 13px;
  line-height: 1.55;
  margin-bottom: 7px;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

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

@media (max-width: 980px) {
  .detail-hero-grid,
  .content-grid,
  .store-info-grid {
    grid-template-columns: 1fr;
  }
  .predict-col { width: 100%; }
}

@media (max-width: 720px) {
  .store-detail-hero { padding: 16px; }
  .detail-toolbar { margin-bottom: 22px; }
  .detail-copy h1 { font-size: 3.1rem; }
  .detail-meta,
  .detail-buy,
  .review-summary,
  .store-data-strip {
    grid-template-columns: 1fr;
  }
  .detail-buy em { justify-self: start; }
  .price-stats { width: 100%; justify-content: space-between; }
  .pstat { align-items: flex-start; }
}
</style>
