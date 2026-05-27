<script setup>
import { computed } from 'vue'

const props = defineProps({
  draw: { type: Object, required: true },
  isLatest: { type: Boolean, default: false },
  sortAdditional: { type: Boolean, default: false },
  colorful: { type: Boolean, default: true },
  // 高亮集合：非空时只有集合内的号显示原色，其它号置黑
  highlight: { type: Set, default: () => new Set() },
})

function bucketClass(n) {
  if (n <= 10) return 'c1'
  if (n <= 19) return 'c2'
  if (n <= 29) return 'c3'
  if (n <= 39) return 'c4'
  return 'c5'
}

function colorClass(n) {
  // search 高亮模式：匹配号一律红色 + 红下划线，其它置黑
  if (props.highlight && props.highlight.size > 0) {
    return props.highlight.has(n) ? 'hl' : 'mono'
  }
  // 无 search：按 Colorful 全彩 / 全黑
  if (!props.colorful) return 'mono'
  return bucketClass(n)
}

const headerDate = computed(() => {
  const [y, m, d] = props.draw.draw_date.split('-')
  return `${d}/${m}/${y} ${props.draw.draw_day || ''}`.trim()
})

const renderNumbers = computed(() => {
  const main = [...props.draw.numbers].sort((a, b) => a - b)
  const add = props.draw.additional_no
  if (props.sortAdditional) {
    const all = [...main.map(n => ({ n, additional: false })), { n: add, additional: true }]
    all.sort((a, b) => a.n - b.n)
    return all
  }
  return [
    ...main.map(n => ({ n, additional: false })),
    { n: add, additional: true },
  ]
})
</script>

<template>
  <div class="card">
    <button class="info-btn" aria-label="详情">i</button>
    <div class="date-row">
      <span class="date">{{ headerDate }}</span>
      <span v-if="isLatest" class="latest">(Latest)</span>
    </div>
    <div class="numbers">
      <span
        v-for="(item, i) in renderNumbers"
        :key="i"
        class="num"
        :class="[colorClass(item.n), { additional: item.additional }]"
      >{{ String(item.n).padStart(2, '0') }}</span>
    </div>
  </div>
</template>

<style scoped>
.card {
  position: relative;
  padding: 18px 16px 22px;
  background: #fff;
}

.date-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-style: italic;
  color: var(--text);
  font-size: 16px;
  margin-bottom: 8px;
}
.latest { font-weight: 600; }
.info-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1.5px solid var(--primary);
  background: transparent;
  color: var(--primary);
  font-style: italic;
  font-weight: 600;
  cursor: pointer;
  line-height: 1;
}

.numbers {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  align-items: baseline;
  font-size: 38px;
  font-weight: 700;
  letter-spacing: -1px;
}
.num.additional { font-style: italic; font-weight: 600; }

/* 颜色 */
.num.c1 { color: var(--color-1-10); }
.num.c2 { color: var(--color-11-19); }
.num.c3 { color: var(--color-20-29); }
.num.c4 { color: var(--color-30-39); }
.num.c5 { color: var(--color-40-49); }
.num.mono { color: var(--text); }

/* search 命中：红字 + 红下划线 */
.num.hl {
  color: var(--danger);
  text-decoration: underline;
  text-decoration-color: var(--danger);
  text-decoration-thickness: 3px;
  text-underline-offset: 4px;
}
</style>
