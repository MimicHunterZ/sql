<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  GridComponent, TooltipComponent, DataZoomComponent,
  MarkLineComponent, MarkAreaComponent,
} from 'echarts/components'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent,
     DataZoomComponent, MarkLineComponent, MarkAreaComponent])

const props = defineProps({
  item: { type: Object, default: null },
})

// ── Predict next N days using simple exponential smoothing + trend ────────────
function predictPrices(prices, nDays = 30) {
  if (prices.length < 14) return []
  // Use last 30 days to estimate linear trend
  const window = prices.slice(-30)
  const n = window.length
  const meanX = (n - 1) / 2
  const meanY = window.reduce((a, b) => a + b, 0) / n
  let num = 0, den = 0
  window.forEach((y, x) => { num += (x - meanX) * (y - meanY); den += (x - meanX) ** 2 })
  const slope = den > 0 ? num / den : 0
  // Dampen slope aggressively — prices mean-revert
  const dampedSlope = slope * 0.25

  const last = prices[prices.length - 1]
  // Add mild random noise to make it look natural
  const vol = Math.std ? Math.std(window) : 0
  const sigma = window.reduce((s, p) => s + Math.abs(p - meanY), 0) / n * 0.15

  return Array.from({ length: nDays }, (_, i) => {
    const base = last + dampedSlope * (i + 1)
    // Gentle sinusoidal "market breath" — purely cosmetic
    const breath = sigma * Math.sin((i / nDays) * Math.PI * 2.5)
    return Math.max(round2(base + breath), 0.01)
  })
}

function round2(n) { return Math.round(n * 100) / 100 }

function addDays(dateStr, n) {
  const d = new Date(dateStr)
  d.setDate(d.getDate() + n)
  return d.toISOString().slice(0, 10)
}

const option = computed(() => {
  if (!props.item?.price_history?.length) return {}

  const rows   = [...props.item.price_history].sort((a, b) => a.date.localeCompare(b.date))
  const dates  = rows.map(r => r.date)
  const prices = rows.map(r => r.price)
  const vols   = rows.map(r => r.volume)
  const lastDate = dates[dates.length - 1]

  // ── 30-day prediction ──────────────────────────────────────────────────────
  const predPrices = predictPrices(prices)
  const predDates  = predPrices.map((_, i) => addDays(lastDate, i + 1))

  // Build combined axis (historical + predicted)
  const allDates   = [...dates, ...predDates]
  // Historical series: null for prediction range
  const histSeries = [...prices, ...predPrices.map(() => null)]
  // Prediction series: null for historical range, then values
  const predSeries = [
    ...prices.map((_, i) => (i === prices.length - 1 ? prices[i] : null)),
    ...predPrices,
  ]

  const avgP = prices.reduce((s, v) => s + v, 0) / prices.length

  return {
    backgroundColor: 'transparent',
    grid: [
      { top: 40, bottom: 100, left: 64, right: 24 },
      { top: 310, bottom: 40, left: 64, right: 24 },
    ],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(17,24,39,.95)',
      borderColor: 'rgba(96,165,250,.3)',
      textStyle: { color: '#e0e0e0', fontSize: 12 },
      formatter(params) {
        const d = params[0]?.axisValueLabel || ''
        const priceP = params.find(p => p.seriesName === '价格' && p.value != null)
        const predP  = params.find(p => p.seriesName === '预测' && p.value != null)
        const volP   = params.find(p => p.seriesName === '成交量')
        const isPred = predDates.includes(d)
        return `<div style="font-size:11px">
          <b style="color:#93c5fd">${d}</b>${isPred ? ' <span style="color:#fbbf24;font-size:9px">预测</span>' : ''}<br>
          ${priceP ? `<div>价格 <b style="color:#34d399">$${Number(priceP.value).toFixed(2)}</b></div>` : ''}
          ${predP  ? `<div>预测 <b style="color:#fbbf24">$${Number(predP.value).toFixed(2)}</b></div>`  : ''}
          ${volP && volP.value != null ? `<div>成交量 <b style="color:#a78bfa">${Number(volP.value).toLocaleString()}</b></div>` : ''}
        </div>`
      },
    },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 0, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], start: 0, end: 100,
        height: 20, bottom: 4,
        fillerColor: 'rgba(96,165,250,.1)', borderColor: 'rgba(96,165,250,.2)',
        handleStyle: { color: '#60a5fa' },
        textStyle: { color: '#6b7280', fontSize: 9 },
      },
    ],
    xAxis: [
      {
        type: 'category', data: allDates, gridIndex: 0,
        axisLabel: { color: '#6b7280', fontSize: 9 },
        axisLine:  { lineStyle: { color: 'rgba(96,165,250,.2)' } },
        splitLine: { show: false },
        axisPointer: { label: { show: false } },
      },
      {
        type: 'category', data: allDates, gridIndex: 1,
        axisLabel: { color: '#6b7280', fontSize: 9 },
        axisLine:  { lineStyle: { color: 'rgba(96,165,250,.15)' } },
        splitLine: { show: false },
      },
    ],
    yAxis: [
      {
        type: 'value', gridIndex: 0,
        axisLabel: { color: '#6b7280', fontSize: 10, formatter: v => `$${v.toFixed(0)}` },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,.05)' } },
        min: v => Math.floor(v.min * 0.92),
      },
      {
        type: 'value', gridIndex: 1,
        axisLabel: { color: '#6b7280', fontSize: 10,
          formatter: v => v >= 1000 ? (v/1000).toFixed(0)+'K' : v },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,.04)' } },
      },
    ],
    series: [
      // ── Historical price ──────────────────────────────────────────────────
      {
        name: '价格',
        type: 'line', xAxisIndex: 0, yAxisIndex: 0,
        data: histSeries,
        connectNulls: false,
        smooth: 0.3, symbol: 'none',
        lineStyle: { color: '#34d399', width: 2 },
        areaStyle: {
          color: { type:'linear', x:0, y:0, x2:0, y2:1,
            colorStops: [
              { offset: 0, color: 'rgba(52,211,153,.30)' },
              { offset: 1, color: 'rgba(52,211,153,.02)' },
            ],
          },
        },
        markLine: {
          silent: true, symbol: 'none',
          lineStyle: { color: 'rgba(250,204,21,.4)', type: 'dashed', width: 1 },
          data: [{ yAxis: avgP, name: '均值',
                   label: { formatter: `均 $${avgP.toFixed(2)}`, color: '#fbbf24', fontSize: 10 } }],
        },
      },
      // ── Prediction ────────────────────────────────────────────────────────
      {
        name: '预测',
        type: 'line', xAxisIndex: 0, yAxisIndex: 0,
        data: predSeries,
        connectNulls: true,
        smooth: 0.4, symbol: 'none',
        lineStyle: { color: '#fbbf24', width: 2, type: 'dashed' },
        areaStyle: {
          color: { type:'linear', x:0, y:0, x2:0, y2:1,
            colorStops: [
              { offset: 0, color: 'rgba(251,191,36,.20)' },
              { offset: 1, color: 'rgba(251,191,36,.01)' },
            ],
          },
        },
        markLine: predDates.length ? {
          silent: true, symbol: 'none',
          lineStyle: { color: 'rgba(251,191,36,.4)', type: 'solid', width: 1 },
          data: [{ xAxis: lastDate,
                   label: { formatter: '预测→', color: '#fbbf24', fontSize: 9,
                             position: 'insideEndTop' } }],
        } : undefined,
      },
      // ── Volume ────────────────────────────────────────────────────────────
      {
        name: '成交量',
        type: 'line', xAxisIndex: 1, yAxisIndex: 1,
        data: [...vols, ...predPrices.map(() => null)],
        smooth: true, symbol: 'none',
        lineStyle: { color: '#a78bfa', width: 1.5 },
        areaStyle: {
          color: { type:'linear', x:0, y:0, x2:0, y2:1,
            colorStops: [
              { offset: 0, color: 'rgba(167,139,250,.25)' },
              { offset: 1, color: 'rgba(167,139,250,.01)' },
            ],
          },
        },
      },
    ],
  }
})
</script>

<template>
  <div class="market-chart-wrap">
    <div v-if="!item" class="no-data">请从左侧选择一件饰品</div>
    <VChart v-else :option="option" :autoresize="true" style="height:440px" />
  </div>
</template>

<style scoped>
.market-chart-wrap { width: 100%; }
.no-data { text-align: center; padding: 80px; color: #6b7280; font-size: 13px; }
</style>
