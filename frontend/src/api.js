import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000',
  timeout: 20000,
})

export async function getOverview() {
  const { data } = await api.get('/api/overview')
  return data
}

export async function getGames() {
  const { data } = await api.get('/api/games')
  return data
}

export async function getTrend(gameId, days = 14) {
  const { data } = await api.get(`/api/trend/${gameId}`, { params: { days } })
  return data
}

export async function getPredict(gameId, discount_rate, update_quality) {
  const { data } = await api.post('/api/predict', {
    gameId,
    discount_rate,
    update_quality,
  })
  return data
}

export async function triggerIngest() {
  const { data } = await api.post('/api/ingest')
  return data
}

// ── Mock-data APIs ─────────────────────────────────────────────────────────────

export async function getHistory(gameId) {
  const { data } = await api.get(`/api/history/${gameId}`)
  return data
}

export async function getCompare(ids) {
  const { data } = await api.get('/api/compare', { params: { ids: ids.join(',') } })
  return data
}

export async function getMarketItems() {
  const { data } = await api.get('/api/market')
  return data
}

export async function getMarketItem(name) {
  const { data } = await api.get('/api/market/item', { params: { name } })
  return data
}

export async function getGameDetail(gameId) {
  const { data } = await api.get(`/api/gamedetail/${gameId}`)
  return data
}

export async function getPrice(gameId) {
  const { data } = await api.get(`/api/price/${gameId}`)
  return data
}

export async function getPredictMonthly(gameId, discountRate = 20, updateQuality = 6) {
  const { data } = await api.get(`/api/predict/monthly/${gameId}`, {
    params: { discount_rate: discountRate, update_quality: updateQuality },
  })
  return data
}
