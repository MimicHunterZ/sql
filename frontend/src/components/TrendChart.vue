<script setup>
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
])

const props = defineProps({
  title: { type: String, default: '' },
  historical: { type: Array, default: () => [] },
  predicted: { type: Array, default: () => [] },
})

function toLabel(dateLike) {
  const d = new Date(dateLike)
  if (Number.isNaN(d.getTime())) return ''
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:00`
}

const option = computed(() => {
  const hist = props.historical.map((p) => ({ label: toLabel(p.ts), value: p.ccu }))
  const pred = props.predicted.map((p, idx) => ({ label: `+${idx + 1}d`, value: p.predicted_ccu }))

  const xAxis = [...hist.map((x) => x.label), ...pred.map((x) => x.label)]
  const histSeries = [...hist.map((x) => x.value), ...new Array(pred.length).fill(null)]
  const predSeries = hist.length > 0
    ? [...new Array(hist.length - 1).fill(null), hist.at(-1)?.value ?? null, ...pred.map((x) => x.value)]
    : pred.map((x) => x.value)

  return {
    backgroundColor: 'transparent',
    title: {
      text: props.title,
      left: 12,
      top: 10,
      textStyle: { 
        color: '#60a5fa', 
        fontSize: 14, 
        fontWeight: 600, 
        fontFamily: 'Inter, sans-serif' 
      },
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(17,24,39,0.95)',
      borderColor: 'rgba(96,165,250,0.5)',
      borderWidth: 1,
      textStyle: { color: '#e0e0e0', fontFamily: 'Inter, sans-serif', fontSize: 12 },
      formatter(params) {
        const active = params.filter((p) => p.value !== null && p.value !== undefined)
        if (!active.length) return ''
        const lines = active.map((p) => `${p.marker}${p.seriesName}: <b>${Number(p.value).toLocaleString()}</b>`)
        return `<div style="font-size:11px">${params[0].axisValue}<br/>${lines.join('<br/>')}</div>`
      },
    },
    legend: {
      top: 10,
      right: 12,
      textStyle: { color: '#d1d5db', fontFamily: 'Inter, sans-serif', fontSize: 11 },
      data: ['历史CCU', '未来7天预测'],
    },
    grid: { left: 60, right: 20, top: 50, bottom: 40 },
    xAxis: {
      type: 'category',
      data: xAxis,
      axisLine: { lineStyle: { color: 'rgba(96,165,250,0.3)' } },
      axisLabel: { color: '#9ca3af', fontSize: 10, fontFamily: 'Inter, sans-serif' },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: 'rgba(96,165,250,0.1)', type: 'dashed' } },
      axisLabel: { color: '#9ca3af', fontSize: 10, fontFamily: 'Inter, sans-serif',
        formatter: (v) => v >= 1000000 ? (v/1000000).toFixed(1)+'M' : v >= 1000 ? (v/1000).toFixed(0)+'K' : v },
    },
    series: [
      {
        name: '历史CCU',
        type: 'line',
        data: histSeries,
        smooth: 0.3,
        showSymbol: false,
        lineStyle: { width: 2.5, color: '#60a5fa' },
        areaStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: 'rgba(96,165,250,0.3)' }, { offset: 1, color: 'rgba(96,165,250,0.01)' }] }
        },
      },
      {
        name: '未来7天预测',
        type: 'line',
        data: predSeries,
        smooth: 0.3,
        showSymbol: false,
        lineStyle: { width: 2.5, type: 'dashed', color: '#a78bfa' },
        areaStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: 'rgba(167,139,250,0.2)' }, { offset: 1, color: 'rgba(167,139,250,0.01)' }] }
        },
      },
    ],
  }
})
</script>

<template>
  <v-chart class="h-[500px] w-full" :option="option" autoresize />
</template>
