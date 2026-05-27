<script setup>
import { onMounted, onBeforeUnmount, ref, watch, computed } from 'vue'
import TopControls from './components/TopControls.vue'
import JackpotBanner from './components/JackpotBanner.vue'
import DrawCard from './components/DrawCard.vue'
import TabBar from './components/TabBar.vue'
import { useDraws } from './composables/useDraws.js'

const sortAdditional = ref(false)
const colorful = ref(true)
const activeTab = ref('toto')

const { items, total, loading, error, done, loadMore } = useDraws({ pageSize: 20 })

// 触底哨兵 + IntersectionObserver
const sentinel = ref(null)
let observer = null

onMounted(async () => {
  await loadMore()  // 首屏
  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) loadMore()
  }, { rootMargin: '200px' })
  if (sentinel.value) observer.observe(sentinel.value)
})
onBeforeUnmount(() => observer?.disconnect())

// 下期开奖估值（DB 还没存这个字段，先用最新一期占位/或简单占位）
const nextJackpot = computed(() => {
  // 没有"下期估值"字段，用最新已知 jackpot 或固定占位
  const first = items.value[0]
  return first?.jackpot_amount ?? 4500000
})
const nextDrawText = computed(() => 'Thu, 28 May 2026, 6.30pm')
</script>

<template>
  <TopControls
    v-model:sortAdditional="sortAdditional"
    v-model:colorful="colorful"
  />

  <JackpotBanner :amount="nextJackpot" :next-draw-text="nextDrawText" />

  <main v-if="activeTab === 'toto'" class="list">
    <DrawCard
      v-for="(d, i) in items"
      :key="d.draw_no"
      :draw="d"
      :is-latest="i === 0"
      :sort-additional="sortAdditional"
      :colorful="colorful"
    />

    <div ref="sentinel" class="sentinel">
      <span v-if="loading">Loading…</span>
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
