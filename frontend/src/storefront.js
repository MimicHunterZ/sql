const CDN_BASE = 'https://cdn.akamai.steamstatic.com/steam/apps'

export function formatCompactNumber(value) {
  if (value == null || Number.isNaN(Number(value))) return '--'
  const n = Number(value)
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toLocaleString()
}

export function formatStorePrice(game) {
  if (game?.is_free) return '免费'
  if (game?.current_cny != null && !Number.isNaN(Number(game.current_cny))) {
    const value = Number(game.current_cny).toFixed(2).replace(/\.00$/, '')
    return `¥${value}`
  }
  if (game?.price_usd != null && Number(game.price_usd) > 0) {
    return `$${Number(game.price_usd).toFixed(2)}`
  }
  return '价格待定'
}

export function gameImage(appid, kind = 'header') {
  const fileByKind = {
    hero: 'capsule_616x353.jpg',
    header: 'header.jpg',
    small: 'capsule_sm_120.jpg',
    library: 'library_600x900.jpg',
  }
  return `${CDN_BASE}/${appid}/${fileByKind[kind] || fileByKind.header}`
}

function scoreGame(game) {
  const ccu = Number(game.current_ccu || 0)
  const tagWeight = (game.tags || []).length * 1800
  const paidBoost = game.is_free ? 0 : 900
  return ccu + tagWeight + paidBoost
}

export function buildStorefrontShelves(games) {
  const catalog = [...(games || [])].sort((a, b) => scoreGame(b) - scoreGame(a))
  const hero = catalog.slice(0, 5)
  const recommended = catalog
    .filter((game) => game.tags?.length || game.current_cny != null || game.price_usd != null)
    .slice(0, 8)
  const trending = [...catalog].sort((a, b) => Number(b.current_ccu || 0) - Number(a.current_ccu || 0)).slice(0, 10)
  const freeToPlay = catalog.filter((game) => game.is_free || game.current_cny === 0).slice(0, 8)

  return { hero, recommended, trending, freeToPlay, catalog }
}

export function searchGames(games, query) {
  const q = String(query || '').trim().toLowerCase()
  if (!q) return []

  return (games || [])
    .filter((game) => {
      const haystack = [
        game.appid,
        game.name,
        ...(game.tags || []),
      ].join(' ').toLowerCase()
      return haystack.includes(q)
    })
    .slice(0, 12)
}
