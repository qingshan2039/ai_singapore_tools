import { ref, computed } from 'vue'
import { fetchDraws } from '../api.js'

export function useDraws({ pageSize = 20 } = {}) {
  const items = ref([])
  const total = ref(0)
  const page = ref(0)         // 已加载到的页数
  const loading = ref(false)
  const error = ref(null)

  // done：至少成功加载过一页(page>0)后，已拿到的条数 >= 总数即完成。
  // 用 page>0 而不是 total>0，这样空库(total=0)在首次加载后 0>=0 → done=true，
  // 不会陷入"total 永远 0 → done 永远 false → 无限请求"的死循环。
  const done = computed(() => page.value > 0 && items.value.length >= total.value)
  const hasMore = computed(() => page.value === 0 || items.value.length < total.value)

  async function loadMore() {
    if (loading.value || done.value) return
    loading.value = true
    error.value = null
    try {
      const next = page.value + 1
      const data = await fetchDraws({ page: next, pageSize })
      // 防重：万一同 page 被请求两次
      const known = new Set(items.value.map(d => d.draw_no))
      const fresh = data.items.filter(d => !known.has(d.draw_no))
      items.value.push(...fresh)
      total.value = data.total
      page.value = next
    } catch (e) {
      error.value = e.message || String(e)
    } finally {
      loading.value = false
    }
  }

  async function reset() {
    items.value = []
    total.value = 0
    page.value = 0
    error.value = null
    await loadMore()
  }

  return { items, total, page, loading, error, hasMore, done, loadMore, reset }
}
