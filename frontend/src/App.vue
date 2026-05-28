<script setup>
import { onMounted, onBeforeUnmount, ref, nextTick, computed } from 'vue'
import TopControls from './components/TopControls.vue'
import DrawCard from './components/DrawCard.vue'
import TabBar from './components/TabBar.vue'
import { useDraws } from './composables/useDraws.js'

const sortAdditional = ref(false)
const colorful = ref(true)
const onlyMatches = ref(false)         // 模式 1：只显示匹配 search 的期
const onlyBigPayout = ref(false)       // 模式 2：只显示 total_payout_corrected > 5.8M
const BIG_PAYOUT_THRESHOLD = 5_800_000
const activeTab = ref('toto')

// === Search 高亮（仍是高亮器；onlyMatches 开启后再变成行过滤器） ===
const searchInput = ref('')

const parsedSearch = computed(() => {
  const raw = searchInput.value.trim()
  if (!raw) return { ok: true, numbers: new Set(), error: '' }
  const tokens = raw.split(/\s+/)
  const numbers = new Set()
  for (const t of tokens) {
    if (!/^\d+$/.test(t)) {
      return { ok: false, numbers: new Set(), error: `"${t}" is not a number` }
    }
    const n = parseInt(t, 10)
    if (n < 1 || n > 49) {
      return { ok: false, numbers: new Set(), error: `${n} is out of range (1-49)` }
    }
    numbers.add(n)
  }
  return { ok: true, numbers, error: '' }
})

const highlight = computed(() =>
  parsedSearch.value.ok ? parsedSearch.value.numbers : new Set()
)
const searchError = computed(() => parsedSearch.value.error)

// === 数据 ===
const { items, total, loading, error, done, loadMore } = useDraws({ pageSize: 50 })

// === 显示过滤（在 loaded items 上做客户端过滤） ===
const matchesFilterActive = computed(() => onlyMatches.value && highlight.value.size > 0)
const filterActive = computed(() => matchesFilterActive.value || onlyBigPayout.value)

const displayedItems = computed(() => {
  let r = items.value
  if (matchesFilterActive.value) {
    const hl = highlight.value
    r = r.filter(d => {
      const all = [...d.numbers, d.additional_no]
      return all.some(n => hl.has(n))
    })
  }
  if (onlyBigPayout.value) {
    r = r.filter(d => (d.total_payout_corrected ?? 0) > BIG_PAYOUT_THRESHOLD)
  }
  return r
})

// === 无限滚动 ===
const sentinel = ref(null)
let observer = null

function isSentinelNearViewport() {
  if (!sentinel.value) return false
  const rect = sentinel.value.getBoundingClientRect()
  return rect.top < window.innerHeight + 400
}

async function loadWhileVisible() {
  // 关键：必须带 !error.value。否则一旦某页请求失败（500/网络断），
  // loadMore 会把 error 置位但 page 不前进、done 仍为 false，
  // 循环条件持续满足 → 无限狂打失败接口。带上 error 检查后，出错即停，
  // 由用户点 Retry 手动恢复。
  while (!done.value && !loading.value && !error.value && isSentinelNearViewport()) {
    await loadMore()
    await nextTick()
  }
}

// Retry：清掉错误后重试当前页，成功则继续自动加载
async function retry() {
  if (loading.value) return
  error.value = null
  await loadMore()
  if (!error.value) await loadWhileVisible()
}

onMounted(async () => {
  await loadMore()
  await loadWhileVisible()
  observer = new IntersectionObserver(
    () => { loadWhileVisible() },
    { rootMargin: '400px' }
  )
  if (sentinel.value) observer.observe(sentinel.value)
})
onBeforeUnmount(() => observer?.disconnect())
</script>

<template>
  <TopControls
    v-model:search="searchInput"
    :search-error="searchError"
    v-model:sortAdditional="sortAdditional"
    v-model:colorful="colorful"
    v-model:onlyMatches="onlyMatches"
    v-model:onlyBigPayout="onlyBigPayout"
    :big-payout-threshold="BIG_PAYOUT_THRESHOLD"
  />

  <main v-if="activeTab === 'toto'" class="list">
    <DrawCard
      v-for="d in displayedItems"
      :key="d.draw_no"
      :draw="d"
      :is-latest="items.length > 0 && d.draw_no === items[0].draw_no"
      :sort-additional="sortAdditional"
      :colorful="colorful"
      :highlight="highlight"
    />

    <div
      v-if="!loading && done && displayedItems.length === 0 && items.length > 0"
      class="empty"
    >
      No draws match the current filters.
    </div>

    <div ref="sentinel" class="sentinel">
      <span v-if="loading">Loading… ({{ items.length }} / {{ total || '?' }})</span>
      <span v-else-if="error" class="err">⚠ {{ error }} <button @click="retry">Retry</button></span>
      <span v-else-if="done" class="done">
        <template v-if="filterActive">— showing {{ displayedItems.length }} of {{ total }} draws —</template>
        <template v-else>— {{ total }} draws loaded —</template>
      </span>
      <span v-else>&nbsp;</span>
    </div>
  </main>

  <main v-else class="placeholder">
    <p>"{{ activeTab.toUpperCase() }}" tab — coming soon.</p>
  </main>

  <TabBar :active="activeTab" @change="activeTab = $event" />
</template>

<style scoped>
.list { display: flex; flex-direction: column; }
.list :deep(.card + .card) { border-top: 1px solid var(--border); }

.empty {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-muted);
  font-size: 14px;
}

.sentinel {
  text-align: center;
  padding: 24px 16px;
  color: var(--text-muted);
  font-size: 14px;
}
.sentinel .err { color: var(--danger); }
.sentinel button { margin-left: 8px; padding: 4px 10px; border: 1px solid var(--primary); color: var(--primary); background: #fff; border-radius: 6px; cursor: pointer; }
.sentinel .done { color: #9aa0a6; }

.placeholder { padding: 40px 16px; text-align: center; color: var(--text-muted); }
</style>
