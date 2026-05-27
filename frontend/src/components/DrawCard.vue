<script setup>
import { computed } from 'vue'

const props = defineProps({
  draw: { type: Object, required: true },
  isLatest: { type: Boolean, default: false },
  sortAdditional: { type: Boolean, default: false },
  colorful: { type: Boolean, default: true },
})

// 颜色按十位分桶，与截图一致
function colorClass(n) {
  if (!props.colorful) return 'mono'
  if (n <= 10) return 'c1'
  if (n <= 19) return 'c2'
  if (n <= 29) return 'c3'
  if (n <= 39) return 'c4'
  return 'c5'
}

// "25/05/2026 Mon" 格式
const headerDate = computed(() => {
  const [y, m, d] = props.draw.draw_date.split('-')
  return `${d}/${m}/${y} ${props.draw.draw_day || ''}`.trim()
})

// 6 个号 + 附加号；如果勾了 "Sort Additional Number"，附加号按数值并入主序
const renderNumbers = computed(() => {
  const main = [...props.draw.numbers].sort((a, b) => a - b)
  const add = props.draw.additional_no
  if (props.sortAdditional) {
    // 把附加号插入排序，但保留 isAdditional 标志（仍用斜体）
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
  <div class="card" :class="{ alt: !isLatest }">
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
.card.alt { background: var(--bg-alt); }

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
</style>
