<script setup>
defineProps({
  amount: { type: [Number, String], default: null },
  nextDrawText: { type: String, default: '' },
})
function formatAmount(v) {
  if (v == null) return '—'
  if (typeof v === 'string') return v
  return '$' + Math.round(v).toLocaleString('en-US') + ' est'
}
</script>

<template>
  <div class="banner">
    <div class="title">
      <span>Next Jackpot: </span>
      <span class="amount">{{ formatAmount(amount) }}</span>
    </div>
    <div v-if="nextDrawText" class="next">{{ nextDrawText }}</div>
  </div>
</template>

<style scoped>
.banner {
  padding: 24px 16px 18px;
  text-align: center;
  background: #fff;
}
.title { font-size: 28px; font-weight: 800; line-height: 1.2; }
.amount { color: var(--danger); }
.next { font-size: 26px; font-weight: 700; margin-top: 4px; }
</style>
