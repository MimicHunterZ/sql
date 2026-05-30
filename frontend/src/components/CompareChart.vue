<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  GridComponent, LegendComponent, TooltipComponent,
  DataZoomComponent,
} from 'echarts/components'

use([CanvasRenderer, LineChart, GridComponent, LegendComponent,
     TooltipComponent, DataZoomComponent])

const props = defineProps({
  // Array of { name, history: [{ month, avg_players }] }
  games: { type: Array, default: () => [] },
})

const COLORS = ['#60a5fa', '#a78bfa', '#34d399', '#f472b6', '#fbbf24']

const option = computed(() => {
  if (!props.games.length) return {}

  // Collect union of all month labels (sorted oldest→newest)
  const monthSet = new Set()
  props.games.forEach(g => {
    ;[...(g.history || [])].forEach(r => monthSet.add(r.month))
  })

  // Sort months chronologically
  const monthList = [...monthSet].sort((a, b) => {
    const parse = s => {
      const months = ['January','February','March','April','May','June',
                      'July','August','September','October','November','December']
      const [mon, yr] = s.split(' ')
      return Number(yr) * 12 + months.indexOf(mon)
    }
    return parse(a) - parse(b)
  })

  const series = props.games.map((g, i) => {
    const map = {}
    ;(g.history || []).forEach(r => { map[r.month] = r.avg_players })
    return {
      name: g.name,
      type: 'line',
      data: monthList.map(m => map[m] ?? null),
      smooth: true,
      symbol: 'none',
      connectNulls: false,
      lineStyle: { color: COLORS[i % COLORS.length], width: 2 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: COLORS[i % COLORS.length].replace(')', ',.18)').replace('rgb', 'rgba') + '' },
            { offset: 1, color: 'rgba(0,0,0,0)' },
          ],
        },
      },
    }
  })

  // Fix areaStyle: build color stops directly
  series.forEach((s, i) => {
    const hex = COLORS[i % COLORS.length]
    s.areaStyle = {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: hexToRgba(hex, 0.25) },
          { offset: 1, color: hexToRgba(hex, 0.01) },
        ],
      },
    }
  })

  return {
    backgroundColor: 'transparent',
    animation: true,
    grid: { top: 48, bottom: 60, left: 60, right: 24 },
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
            `<div style="display:flex;justify-content:space-between;gap:20px">
              <span style="color:${p.color}">${p.seriesName}</span>
              <b>${Number(p.value).toLocaleString()}</b>
             </div>`
          ).join('')
        return `<div style="font-size:11px;min-width:200px"><b style="color:#93c5fd">${m}</b><br>${lines}</div>`
      },
    },
    legend: {
      top: 4, right: 0,
      textStyle: { color: '#9ca3af', fontSize: 11 },
      itemWidth: 20, itemHeight: 3,
    },
    dataZoom: [
      { type: 'inside', start: 50, end: 100 },
      { type: 'slider', start: 50, end: 100, height: 20, bottom: 4,
        fillerColor: 'rgba(96,165,250,.1)',
        borderColor: 'rgba(96,165,250,.2)',
        handleStyle: { color: '#60a5fa' },
        textStyle: { color: '#6b7280', fontSize: 9 },
      },
    ],
    xAxis: {
      type: 'category',
      data: monthList,
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
      splitLine: { lineStyle: { color: 'rgba(255,255,255,.05)' } },
    },
    series,
  }
})

function hexToRgba(hex, alpha) {
  const h = hex.replace('#', '')
  const r = parseInt(h.slice(0,2), 16)
  const g = parseInt(h.slice(2,4), 16)
  const b = parseInt(h.slice(4,6), 16)
  return `rgba(${r},${g},${b},${alpha})`
}
</script>

<template>
  <div class="compare-chart-wrap">
    <div v-if="!games.length" class="no-data">请至少选择一款游戏</div>
    <VChart v-else :option="option" :autoresize="true" style="height:380px" />
  </div>
</template>

<style scoped>
.compare-chart-wrap { width: 100%; }
.no-data { text-align: center; padding: 80px; color: #6b7280; font-size: 13px; }
</style>
