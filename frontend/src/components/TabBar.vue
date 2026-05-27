<script setup>
defineProps({
  active: { type: String, default: 'toto' },
})
defineEmits(['change'])

const tabs = [
  { id: 'toto',     label: 'TOTO',     icon: 'M' },
  { id: '4d',       label: '4D',       icon: 'C' },
  { id: 'sweep',    label: 'SWEEP',    icon: '$' },
  { id: 'stats',    label: 'Stats',    icon: '#' },
  { id: 'settings', label: 'Settings', icon: 'G' },
]
</script>

<template>
  <nav class="tabbar">
    <button
      v-for="t in tabs"
      :key="t.id"
      class="tab"
      :class="{ active: active === t.id }"
      @click="$emit('change', t.id)"
    >
      <span class="icon">{{ t.icon }}</span>
      <span class="label">{{ t.label }}</span>
    </button>
  </nav>
</template>

<style scoped>
.tabbar {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  display: flex;
  background: #fff;
  border-top: 1px solid var(--border);
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 10;
}
.tab {
  flex: 1;
  border: none;
  background: transparent;
  padding: 8px 0 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  color: #8a8f98;
  cursor: pointer;
  font-size: 12px;
}
.tab .icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: #eef0f3;
  color: #6b7280;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}
.tab.active { color: var(--primary); }
.tab.active .icon { background: var(--primary); color: #fff; }
.tab .label { font-size: 12px; }
</style>
