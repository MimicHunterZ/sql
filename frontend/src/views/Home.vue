<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getGames, getOverview } from '../api'
import { buildStorefrontShelves, formatCompactNumber, formatStorePrice, gameImage, searchGames } from '../storefront'

const router = useRouter()
const loading = ref(true)
const errorMsg = ref('')
const query = ref('')
const games = ref([])
const overview = ref({ monitored_games: 0 })
const activeHero = ref(0)
let carouselTimer = null

const shelves = computed(() => buildStorefrontShelves(games.value))
const heroGame = computed(() => shelves.value.hero[activeHero.value] || shelves.value.hero[0])
const searchResults = computed(() => searchGames(games.value, query.value))

function goGame(game) {
  if (!game?.appid) return
  router.push(`/game/${game.appid}`)
}

function nextHero(offset) {
  const total = shelves.value.hero.length
  if (!total) return
  activeHero.value = (activeHero.value + offset + total) % total
}

function submitSearch() {
  if (searchResults.value.length) goGame(searchResults.value[0])
}

onMounted(async () => {
  try {
    const [ov, gm] = await Promise.all([getOverview(), getGames()])
    overview.value = ov
    games.value = gm
    carouselTimer = setInterval(() => nextHero(1), 5600)
  } catch (e) {
    errorMsg.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  if (carouselTimer) clearInterval(carouselTimer)
})
</script>

<template>
  <div class="store-home">
    <header class="store-topbar">
      <div>
        <p class="store-kicker">STEAM CCU STORE</p>
        <h1>精选与趋势</h1>
      </div>
      <form class="store-search" @submit.prevent="submitSearch">
        <input
          v-model="query"
          type="search"
          placeholder="搜索游戏、标签或 AppID"
          autocomplete="off"
        />
        <button type="submit" aria-label="搜索">⌕</button>
        <div v-if="query.trim()" class="search-popover">
          <button
            v-for="game in searchResults"
            :key="game.appid"
            type="button"
            class="search-hit"
            @click="goGame(game)"
          >
            <img :src="gameImage(game.appid, 'small')" :alt="game.name" />
            <span>
              <b>{{ game.name }}</b>
              <small>{{ (game.tags || []).slice(0, 2).join(' / ') || `App ${game.appid}` }}</small>
            </span>
            <em>{{ formatCompactNumber(game.current_ccu) }}</em>
          </button>
          <p v-if="!searchResults.length" class="search-empty">没有找到匹配游戏</p>
        </div>
      </form>
    </header>

    <div v-if="loading" class="store-state">加载商店数据...</div>
    <div v-else-if="errorMsg" class="store-state store-state--error">{{ errorMsg }}</div>

    <template v-else>
      <section
        v-if="heroGame"
        class="hero-stage"
        :style="{ backgroundImage: `linear-gradient(90deg, rgba(8,13,20,.96) 0%, rgba(8,13,20,.7) 46%, rgba(8,13,20,.2) 100%), url(${gameImage(heroGame.appid, 'hero')})` }"
      >
        <div class="hero-copy">
          <p class="store-kicker">FEATURED GAME</p>
          <h2>{{ heroGame.name }}</h2>
          <p class="hero-desc">
            {{ (heroGame.tags || []).slice(0, 4).join(' · ') || 'Steam 热门游戏' }}
          </p>
          <div class="hero-stats">
            <span>{{ formatCompactNumber(heroGame.current_ccu) }} 当前在线</span>
            <span>{{ formatStorePrice(heroGame) }}</span>
            <span>App {{ heroGame.appid }}</span>
          </div>
          <button class="hero-cta" @click="goGame(heroGame)">查看详情</button>
        </div>

        <div class="hero-panel">
          <button
            v-for="(game, index) in shelves.hero"
            :key="game.appid"
            class="hero-thumb"
            :class="{ 'hero-thumb--active': index === activeHero }"
            type="button"
            @click="activeHero = index"
          >
            <img :src="gameImage(game.appid, 'header')" :alt="game.name" />
            <span>{{ game.name }}</span>
          </button>
        </div>

        <button class="hero-step hero-step--prev" type="button" @click="nextHero(-1)" aria-label="上一张">‹</button>
        <button class="hero-step hero-step--next" type="button" @click="nextHero(1)" aria-label="下一张">›</button>
      </section>

      <section class="store-metrics">
        <div>
          <span>监控游戏</span>
          <b>{{ overview.monitored_games || shelves.catalog.length }}</b>
        </div>
        <div>
          <span>今日峰值</span>
          <b>{{ overview.top_game_name || shelves.trending[0]?.name || '--' }}</b>
        </div>
        <div>
          <span>峰值 CCU</span>
          <b>{{ formatCompactNumber(overview.top_game_ccu || shelves.trending[0]?.current_ccu) }}</b>
        </div>
      </section>

      <section class="shelf">
        <div class="shelf-head">
          <p class="store-kicker">RECOMMENDED</p>
          <h2>为你推荐</h2>
        </div>
        <div class="poster-grid">
          <button
            v-for="game in shelves.recommended"
            :key="game.appid"
            class="poster-card"
            type="button"
            @click="goGame(game)"
          >
            <img :src="gameImage(game.appid, 'hero')" :alt="game.name" />
            <span class="poster-body">
              <b>{{ game.name }}</b>
              <small>{{ (game.tags || []).slice(0, 3).join(' · ') || '精选游戏' }}</small>
              <em>{{ formatStorePrice(game) }}</em>
            </span>
          </button>
        </div>
      </section>

      <section class="store-columns">
        <div class="rank-shelf">
          <div class="shelf-head">
            <p class="store-kicker">TRENDING</p>
            <h2>热门在线</h2>
          </div>
          <button
            v-for="(game, index) in shelves.trending"
            :key="game.appid"
            class="rank-row"
            type="button"
            @click="goGame(game)"
          >
            <span class="rank-no">{{ index + 1 }}</span>
            <img :src="gameImage(game.appid, 'small')" :alt="game.name" />
            <b>{{ game.name }}</b>
            <em>{{ formatCompactNumber(game.current_ccu) }}</em>
          </button>
        </div>

        <div class="rank-shelf">
          <div class="shelf-head">
            <p class="store-kicker">FREE TO PLAY</p>
            <h2>免费开玩</h2>
          </div>
          <button
            v-for="game in shelves.freeToPlay"
            :key="game.appid"
            class="rank-row"
            type="button"
            @click="goGame(game)"
          >
            <img :src="gameImage(game.appid, 'small')" :alt="game.name" />
            <b>{{ game.name }}</b>
            <small>{{ (game.tags || []).slice(0, 2).join(' / ') }}</small>
          </button>
        </div>
      </section>

      <section class="shelf">
        <div class="shelf-head">
          <p class="store-kicker">CATALOG</p>
          <h2>全部游戏</h2>
        </div>
        <div class="catalog-grid">
          <button
            v-for="game in shelves.catalog"
            :key="game.appid"
            class="catalog-card"
            type="button"
            @click="goGame(game)"
          >
            <img :src="gameImage(game.appid, 'header')" :alt="game.name" />
            <span>
              <b>{{ game.name }}</b>
              <small>{{ formatCompactNumber(game.current_ccu) }} 在线</small>
            </span>
          </button>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.store-home {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 1360px;
  margin: 0 auto;
}

.store-topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 10px 0 16px;
  background: linear-gradient(180deg, rgba(9, 14, 22, .98), rgba(9, 14, 22, .74) 70%, transparent);
  backdrop-filter: blur(16px);
}

.store-kicker {
  color: #67c1f5;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .12em;
  text-transform: uppercase;
}

.store-topbar h1,
.shelf-head h2 {
  font-family: 'Barlow Condensed', 'Noto Sans SC', sans-serif;
  color: #f3f7fb;
  line-height: 1;
  letter-spacing: 0;
}

.store-topbar h1 { font-size: clamp(2.1rem, 4vw, 4.2rem); }
.shelf-head h2 { font-size: 1.7rem; margin-top: 4px; }

.store-search {
  position: relative;
  display: flex;
  min-width: min(420px, 42vw);
  height: 42px;
  border: 1px solid rgba(103, 193, 245, .36);
  background: rgba(20, 43, 66, .78);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.04), 0 16px 40px rgba(0,0,0,.26);
}

.store-search input {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: #eaf6ff;
  padding: 0 12px;
  font-size: 14px;
}

.store-search input::placeholder { color: rgba(196, 220, 238, .62); }

.store-search button[type="submit"] {
  width: 46px;
  border: 0;
  color: #10202f;
  background: linear-gradient(135deg, #9de7ff, #66c0f4);
  font-size: 22px;
  cursor: pointer;
}

.search-popover {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  padding: 8px;
  background: rgba(12, 22, 34, .98);
  border: 1px solid rgba(103, 193, 245, .32);
  box-shadow: 0 24px 70px rgba(0,0,0,.45);
}

.search-hit {
  display: grid;
  grid-template-columns: 86px 1fr auto;
  align-items: center;
  gap: 10px;
  width: 100%;
  border: 0;
  background: transparent;
  color: #e8eef5;
  text-align: left;
  padding: 7px;
  cursor: pointer;
}

.search-hit:hover { background: rgba(103, 193, 245, .14); }
.search-hit img { width: 86px; height: 40px; object-fit: cover; }
.search-hit b, .search-hit small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.search-hit small, .search-hit em { color: #8f98a0; font-style: normal; font-size: 12px; }
.search-empty { padding: 18px 10px; color: #8f98a0; font-size: 13px; }

.store-state {
  display: grid;
  place-items: center;
  min-height: 340px;
  color: #8f98a0;
  border: 1px solid rgba(103,193,245,.18);
  background: rgba(16, 31, 46, .65);
}
.store-state--error { color: #f87171; }

.hero-stage {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 310px;
  min-height: 440px;
  overflow: hidden;
  background-size: cover;
  background-position: center;
  border: 1px solid rgba(103, 193, 245, .22);
  box-shadow: 0 32px 90px rgba(0, 0, 0, .36);
}

.hero-stage::after {
  content: '';
  position: absolute;
  inset: auto 0 0;
  height: 3px;
  background: linear-gradient(90deg, #67c1f5, #a4d007, #f5c451);
}

.hero-copy {
  position: relative;
  z-index: 1;
  align-self: end;
  max-width: 780px;
  padding: 44px;
}

.hero-copy h2 {
  font-family: 'Barlow Condensed', 'Noto Sans SC', sans-serif;
  font-size: clamp(3rem, 6vw, 6.8rem);
  line-height: .86;
  color: #ffffff;
  margin: 10px 0 16px;
  text-shadow: 0 10px 40px rgba(0,0,0,.5);
}

.hero-desc {
  color: #c7d5e0;
  font-size: 18px;
  margin-bottom: 18px;
}

.hero-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 24px;
}

.hero-stats span {
  padding: 7px 11px;
  color: #dfe9f3;
  background: rgba(0,0,0,.34);
  border: 1px solid rgba(255,255,255,.1);
  font-size: 12px;
}

.hero-cta {
  border: 0;
  color: #0f1b24;
  background: linear-gradient(135deg, #b7e433, #75b022);
  padding: 11px 22px;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 12px 30px rgba(117,176,34,.28);
}

.hero-panel {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 9px;
  padding: 28px 28px 28px 0;
  align-self: center;
}

.hero-thumb {
  display: grid;
  grid-template-columns: 104px 1fr;
  align-items: center;
  gap: 12px;
  min-height: 58px;
  border: 1px solid rgba(255,255,255,.08);
  background: rgba(8, 13, 20, .64);
  color: #c7d5e0;
  text-align: left;
  cursor: pointer;
  transition: transform .2s, border-color .2s, background .2s;
}

.hero-thumb:hover,
.hero-thumb--active {
  transform: translateX(-8px);
  border-color: rgba(103,193,245,.64);
  background: linear-gradient(90deg, rgba(37, 74, 104, .88), rgba(8, 13, 20, .72));
  color: #fff;
}

.hero-thumb img { width: 104px; height: 48px; object-fit: cover; }
.hero-thumb span { font-weight: 700; font-size: 13px; padding-right: 10px; }

.hero-step {
  position: absolute;
  top: 50%;
  z-index: 2;
  width: 38px;
  height: 72px;
  border: 0;
  color: #fff;
  background: rgba(0,0,0,.28);
  font-size: 42px;
  cursor: pointer;
  transform: translateY(-50%);
}
.hero-step--prev { left: 0; }
.hero-step--next { right: 0; }

.store-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.store-metrics div {
  min-width: 0;
  padding: 18px 20px;
  background: rgba(20, 43, 66, .74);
  border: 1px solid rgba(103,193,245,.18);
}

.store-metrics span {
  display: block;
  color: #8f98a0;
  font-size: 12px;
  margin-bottom: 8px;
}

.store-metrics b {
  display: block;
  color: #f3f7fb;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: 'Barlow Condensed', 'Noto Sans SC', sans-serif;
  font-size: 1.7rem;
}

.shelf,
.rank-shelf {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.poster-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.poster-card {
  display: flex;
  flex-direction: column;
  min-width: 0;
  border: 1px solid rgba(103, 193, 245, .15);
  background: #17202c;
  color: #e8eef5;
  text-align: left;
  cursor: pointer;
  transition: transform .2s, box-shadow .2s, border-color .2s;
}

.poster-card:hover {
  transform: translateY(-5px);
  border-color: rgba(103,193,245,.5);
  box-shadow: 0 18px 50px rgba(0,0,0,.38);
}

.poster-card img {
  width: 100%;
  aspect-ratio: 616 / 353;
  object-fit: cover;
}

.poster-body {
  display: grid;
  gap: 5px;
  padding: 12px;
}

.poster-body b,
.poster-body small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.poster-body small { color: #8f98a0; }
.poster-body em { color: #b7e433; font-style: normal; font-weight: 800; }

.store-columns {
  display: grid;
  grid-template-columns: 1.1fr .9fr;
  gap: 18px;
}

.rank-row,
.catalog-card {
  border: 0;
  color: #dfe3e6;
  background: rgba(20, 43, 66, .58);
  cursor: pointer;
  transition: background .18s, transform .18s;
}

.rank-row {
  display: grid;
  grid-template-columns: 34px 90px 1fr auto;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  text-align: left;
}

.rank-shelf:nth-child(2) .rank-row {
  grid-template-columns: 90px 1fr auto;
}

.rank-row:hover,
.catalog-card:hover {
  background: rgba(103, 193, 245, .16);
  transform: translateX(4px);
}

.rank-no {
  font-family: 'Barlow Condensed', sans-serif;
  color: #67c1f5;
  font-size: 20px;
  font-weight: 800;
}

.rank-row img { width: 90px; height: 42px; object-fit: cover; }
.rank-row b { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rank-row em, .rank-row small { color: #8f98a0; font-style: normal; font-size: 12px; }

.catalog-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.catalog-card {
  display: grid;
  grid-template-columns: 132px 1fr;
  align-items: center;
  gap: 10px;
  padding: 8px;
  text-align: left;
}

.catalog-card img { width: 132px; height: 62px; object-fit: cover; }
.catalog-card b, .catalog-card small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.catalog-card small { color: #8f98a0; margin-top: 3px; }

@media (max-width: 1040px) {
  .hero-stage { grid-template-columns: 1fr; }
  .hero-panel {
    display: grid;
    grid-template-columns: repeat(5, minmax(110px, 1fr));
    padding: 0 20px 26px;
    overflow-x: auto;
  }
  .hero-thumb { grid-template-columns: 1fr; }
  .hero-thumb img { width: 100%; }
  .poster-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .store-columns, .catalog-grid { grid-template-columns: 1fr; }
}

@media (max-width: 720px) {
  .store-topbar {
    position: relative;
    flex-direction: column;
    align-items: stretch;
  }
  .store-search { min-width: 0; width: 100%; }
  .hero-copy { padding: 34px 22px; }
  .hero-copy h2 { font-size: 3.1rem; }
  .store-metrics, .poster-grid { grid-template-columns: 1fr; }
  .catalog-card { grid-template-columns: 104px 1fr; }
  .catalog-card img { width: 104px; height: 50px; }
}
</style>
