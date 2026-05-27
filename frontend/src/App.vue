<script setup>
import { onMounted, onBeforeUnmount, ref, nextTick } from 'vue'
import TopControls from './components/TopControls.vue'
import DrawCard from './components/DrawCard.vue'
import TabBar from './components/TabBar.vue'
import { useDraws } from './composables/useDraws.js'

const sortAdditional = ref(false)
const colorful = ref(true)
const activeTab = ref('toto')

const { items, total, loading, error, done, loadMore } = useDraws({ pageSize: 50 })

// === 无限滚动 ===
// 关键 bug 修复：IntersectionObserver 的 callback 只在 isIntersecting 状态
// 翻转时触发。如果首屏太短、sentinel 一直在视口里，加载完一页后状态没变
// → 回调不会再触发 → 看起来只加载一页就停了。
// 解决：每次回调里用 while-loop + 几何位置判断，主动连续加载直到 sentinel
// 不可见或已全部加载。
const sentinel = ref(null)
let observer = null

function isSentinelNearViewport() {
  if (!sentinel.value) return false
  const rect = sentinel.value.getBoundingClientRect()
  // rootMargin 400px → 距离视口底部 400px 内就算可见
  return rect.top < window.innerHeight + 400
}

async function loadWhileVisible() {
  while (!done.value && !loading.value && isSentinelNearViewport()) {
    await loadMore()
    await nextTick()  // 等 DOM 渲染后再判断几何位置
  }
}

onMounted(async () => {
  await loadMore()        // 首屏
  await loadWhileVisible() // 万一首屏不够撑满，再补几页
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
