<script setup>
import { onMounted, onBeforeUnmount, ref, nextTick, computed } from 'vue'
import TopControls from './components/TopControls.vue'
import DrawCard from './components/DrawCard.vue'
import TabBar from './components/TabBar.vue'
import { useDraws } from './composables/useDraws.js'

const sortAdditional = ref(false)
const colorful = ref(true)
const activeTab = ref('toto')

// === Search 高亮 ===
// 规则：
// - 空字符串 → 不生效，列表按 colorful 显示
// - 用空白分隔的数字 token，每个必须 ∈ [1, 49]
// - 任一 token 非法 → 整体不生效 + 显示错误（行为可预测）
// - 全部合法 → 列表中仅匹配号显示原色，其余置黑
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

const { items, total, loading, error, done, loadMore } = useDraws({ pageSize: 50 })

// === 无限滚动 ===
const sentinel = ref(null)
let observer = null

function isSentinelNearViewport() {
  if (!sentinel.value) return false
  const rect = sentinel.value.getBoundingClientRect()
  return rect.top < window.innerHeight + 400
}

async function loadWhileVisible() {
  while (!done.value && !loading.value && isSentinelNearViewport()) {
    await loadMore()
    await nextTick()
  }
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
  />

  <main v-if="activeTab === 'toto'" class="list">
    <DrawCard
      v-for="(d, i) in items"
      :key="d.draw_no"
      :draw="d"
      :is-latest="i === 0"
      :sort-additional="sortAdditional"
      :colorful="colorful"
      :highlight="highlight"
    />

    <div ref="sentinel" class="sentinel">
      <span v-if="loading">Loading… ({{ items.length }} / {{ total || '?' }})</span>
      <span v-else-if="error" class="err">⚠ {{ error }} <button @click="loadMore">Retry</button></span>
      <span v-else-if="done" class="done">— {{ total }} draws loaded —</span>
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
