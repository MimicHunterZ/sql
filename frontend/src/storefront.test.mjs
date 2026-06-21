import assert from 'node:assert/strict'
import { buildStorefrontShelves, formatCompactNumber, formatStorePrice, gameImage, searchGames } from './storefront.js'

const games = [
  { appid: 730, name: 'Counter-Strike 2', current_ccu: 1220751, tags: ['FPS', '竞技'], is_free: true, current_cny: 0 },
  { appid: 570, name: 'Dota 2', current_ccu: 562224, tags: ['MOBA', '策略'], is_free: true, current_cny: 0 },
  { appid: 1086940, name: '博德之门3', current_ccu: null, tags: ['角色扮演', '冒险'], is_free: false, current_cny: 298 },
  { appid: 1245620, name: '艾尔登法环', current_ccu: 80000, tags: ['动作', '角色扮演'], is_free: false, current_cny: 298 },
]

assert.equal(formatCompactNumber(1220751), '1.22M')
assert.equal(formatCompactNumber(562224), '562.2K')
assert.equal(formatCompactNumber(null), '--')

assert.equal(gameImage(730, 'header'), 'https://cdn.akamai.steamstatic.com/steam/apps/730/header.jpg')
assert.equal(formatStorePrice({ is_free: true, current_cny: 0 }), '免费')
assert.equal(formatStorePrice({ is_free: false, current_cny: 12.4 }), '¥12.40')
assert.equal(formatStorePrice({ is_free: false, current_cny: 119 }), '¥119')

assert.deepEqual(searchGames(games, 'dota').map((g) => g.appid), [570])
assert.deepEqual(searchGames(games, '角色').map((g) => g.appid), [1086940, 1245620])
assert.deepEqual(searchGames(games, '730').map((g) => g.appid), [730])
assert.deepEqual(searchGames(games, '   '), [])

const shelves = buildStorefrontShelves(games)
assert.deepEqual(shelves.hero.map((g) => g.appid), [730, 570, 1245620, 1086940])
assert.deepEqual(shelves.freeToPlay.map((g) => g.appid), [730, 570])
assert.equal(shelves.catalog.length, 4)
