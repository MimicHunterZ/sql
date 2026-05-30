<script setup>
import { computed, onMounted, ref } from 'vue'
import MarketChart from '../components/MarketChart.vue'
import { getMarketItems, getMarketItem } from '../api'

const loading      = ref(true)
const loadingItem  = ref(false)
const items        = ref([])
const selectedName = ref('')
const itemDetail   = ref(null)
const activeCategory = ref('全部')

const CATEGORY_ORDER = ['全部', '刀具', '手套', 'AK-47', 'AWP', 'M4A1-S', 'M4A4', 'USP-S', '沙漠之鹰']

const categories = computed(() => {
  const cats = [...new Set(items.value.map(i => i.category).filter(Boolean))]
  return ['全部', ...CATEGORY_ORDER.slice(1).filter(c => cats.includes(c))]
})

const filteredItems = computed(() =>
  activeCategory.value === '全部'
    ? items.value
    : items.value.filter(i => i.category === activeCategory.value)
)

function fmtPrice(n) {
  if (n == null) return '--'
  return `$${Number(n).toFixed(2)}`
}
function changeClass(pct) {
  if (pct > 0)  return 'badge badge-up'
  if (pct < 0)  return 'badge badge-down'
  return 'badge badge-flat'
}
function changeText(pct) {
  if (pct == null) return '--'
  const s = Number(pct).toFixed(2)
  return pct >= 0 ? `+${s}%` : `${s}%`
}

async function selectItem(name) {
  if (selectedName.value === name) return
  selectedName.value = name
  loadingItem.value  = true
  try {
    itemDetail.value = await getMarketItem(name)
  } catch {
    itemDetail.value = null
  } finally {
    loadingItem.value = false
  }
}

function switchCategory(cat) {
  activeCategory.value = cat
  // auto-select first item in category
  const first = filteredItems.value[0]
  if (first && first.name !== selectedName.value) selectItem(first.name)
}

onMounted(async () => {
  try {
    items.value = await getMarketItems()
    if (items.value.length) await selectItem(items.value[0].name)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="market-page">

    <div class="page-header">
      <div>
        <h1 class="page-title">CS2 饰品市场</h1>
        <p class="page-sub">{{ items.length }} 件饰品 · 180 天历史走势 · 实时成交量</p>
      </div>
    </div>

    <div v-if="loading" class="loading-block">加载中...</div>
    <div v-else class="market-layout">

      <!-- left: category tabs + item list -->
      <div class="glass-card items-card">

        <!-- category tabs -->
        <div class="cat-tabs">
          <button
            v-for="cat in categories"
            :key="cat"
            class="cat-tab"
            :class="{ 'cat-tab--active': activeCategory === cat }"
            @click="switchCategory(cat)"
          >{{ cat }}</button>
        </div>

        <!-- item list -->
        <div class="items-list">
          <button
            v-for="item in filteredItems"
            :key="item.name"
            class="item-row"
            :class="{ 'item-row--active': selectedName === item.name }"
            @click="selectItem(item.name)"
          >
            <!-- item image -->
            <div class="item-img-wrap">
              <img
                v-if="item.image_url"
                :src="item.image_url"
                :alt="item.name"
                class="item-img"
                loading="lazy"
              />
              <div v-else class="item-img-placeholder">?</div>
            </div>

            <div class="item-info">
              <span class="item-name">{{ item.name }}</span>
              <div class="item-badges">
                <span :class="changeClass(item.change_7d)" style="font-size:9px">
                  7d {{ changeText(item.change_7d) }}
                </span>
                <span :class="changeClass(item.change_30d)" style="font-size:9px">
                  30d {{ changeText(item.change_30d) }}
                </span>
              </div>
            </div>
            <div class="item-price-col">
              <span class="item-price">{{ fmtPrice(item.current_price) }}</span>
            </div>
          </button>
        </div>
      </div>

      <!-- right: chart -->
      <div class="chart-area">
        <div class="glass-card chart-card" v-if="selectedName">
          <div class="chart-header">
            <!-- selected item image + name -->
            <div class="chart-title-row">
              <img
                v-if="itemDetail?.image_url"
                :src="itemDetail.image_url"
                class="chart-item-img"
                :alt="itemDetail.name"
              />
              <p class="section-label" style="margin-bottom:0;border:none;padding:0">{{ selectedName }}</p>
            </div>
            <div v-if="itemDetail" class="price-stats">
              <div class="pstat">
                <span class="pstat-label">当前</span>
                <span class="pstat-val" style="color:#34d399">{{ fmtPrice(itemDetail.current_price) }}</span>
              </div>
              <div class="pstat">
                <span class="pstat-label">7日</span>
                <span :class="changeClass(itemDetail.change_7d)" class="pstat-badge">{{ changeText(itemDetail.change_7d) }}</span>
              </div>
              <div class="pstat">
                <span class="pstat-label">30日</span>
                <span :class="changeClass(itemDetail.change_30d)" class="pstat-badge">{{ changeText(itemDetail.change_30d) }}</span>
              </div>
            </div>
          </div>
          <div style="margin-top:16px">
            <div v-if="loadingItem" class="loading-msg">加载图表数据...</div>
            <MarketChart v-else :item="itemDetail" />
          </div>
        </div>
        <div v-else class="glass-card chart-card empty-chart">
          <p style="color:#6b7280;font-size:13px">请从左侧选择饰品</p>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.market-page { display: flex; flex-direction: column; gap: 20px; }
.loading-block { text-align: center; padding: 80px; color: #6b7280; font-size: 13px; }

.market-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 16px;
  align-items: start;
}

/* ── Category tabs ─────────────────────────────────────────────────── */
.items-card { padding: 16px; }

.cat-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}
.cat-tab {
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid rgba(96,165,250,.2);
  background: transparent;
  color: #6b7280;
  font-size: 11px;
  cursor: pointer;
  transition: all .15s;
}
.cat-tab:hover { border-color: rgba(96,165,250,.5); color: #93c5fd; }
.cat-tab--active {
  background: rgba(96,165,250,.15);
  border-color: rgba(96,165,250,.6);
  color: #93c5fd;
  font-weight: 600;
}

/* ── Item list ─────────────────────────────────────────────────────── */
.items-list { display: flex; flex-direction: column; gap: 4px; max-height: 70vh; overflow-y: auto; }

.item-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 8px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: rgba(0,0,0,.2);
  color: #d1d5db;
  cursor: pointer;
  transition: all .15s;
  text-align: left;
  width: 100%;
}
.item-row:hover { border-color: rgba(96,165,250,.3); background: rgba(96,165,250,.07); }
.item-row--active { border-color: rgba(52,211,153,.5); background: rgba(52,211,153,.08); }

.item-img-wrap { flex-shrink: 0; width: 52px; height: 38px; display: flex; align-items: center; justify-content: center; }
.item-img {
  width: 52px;
  height: 38px;
  object-fit: contain;
  border-radius: 4px;
  background: rgba(0,0,0,.3);
}
.item-img-placeholder {
  width: 52px; height: 38px;
  display: flex; align-items: center; justify-content: center;
  color: #374151; font-size: 18px;
  background: rgba(0,0,0,.2); border-radius: 4px;
}

.item-info { display: flex; flex-direction: column; gap: 3px; flex: 1; min-width: 0; }
.item-name {
  font-size: 11px; font-weight: 500; color: #e0e0e0;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.item-row--active .item-name { color: #6ee7b7; }
.item-badges { display: flex; gap: 4px; flex-wrap: wrap; }

.item-price-col { flex-shrink: 0; }
.item-price {
  font-family: 'Rajdhani', sans-serif; font-size: 14px; font-weight: 700; color: var(--cyan);
}
.item-row--active .item-price { color: #34d399; }

/* ── Chart area ────────────────────────────────────────────────────── */
.chart-area {}
.chart-card { padding: 20px; }
.empty-chart { display: flex; align-items: center; justify-content: center; min-height: 200px; }

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border);
}
.chart-title-row { display: flex; align-items: center; gap: 12px; }
.chart-item-img {
  width: 80px; height: 58px;
  object-fit: contain;
  border-radius: 6px;
  background: rgba(0,0,0,.3);
  border: 1px solid rgba(255,255,255,.08);
}

.price-stats { display: flex; gap: 16px; align-items: center; }
.pstat { display: flex; align-items: center; gap: 6px; }
.pstat-label { font-size: 10px; color: #6b7280; letter-spacing: .05em; }
.pstat-val  { font-family: 'Rajdhani', sans-serif; font-size: 15px; font-weight: 700; }
.pstat-badge { font-size: 11px; }

.loading-msg { text-align: center; padding: 60px; color: #6b7280; font-size: 13px; }
</style>
