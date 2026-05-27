<script setup>
import { computed } from 'vue'

const props = defineProps({
  search: { type: String, default: '' },
  searchError: { type: String, default: '' },
  sortAdditional: Boolean,
  colorful: Boolean,
  onlyMatches: Boolean,
  onlyBigPayout: Boolean,
  bigPayoutThreshold: { type: Number, default: 5_800_000 },
})
defineEmits([
  'update:search',
  'update:sortAdditional',
  'update:colorful',
  'update:onlyMatches',
  'update:onlyBigPayout',
])

const bigPayoutLabel = computed(() => {
  const m = props.bigPayoutThreshold / 1_000_000
  return `Big payouts (>$${m.toFixed(1)}M)`
})
</script>

<template>
  <div class="top">
    <div class="search-row">
      <input
        type="text"
        :value="search"
        @input="$emit('update:search', $event.target.value)"
        :class="{ invalid: !!searchError }"
        placeholder="Highlight numbers — e.g. 11 22 35"
        inputmode="numeric"
        aria-label="Highlight numbers"
      />
    </div>
    <div v-if="searchError" class="error">{{ searchError }}</div>

    <div class="toggles">
      <label>
        <input
          type="checkbox"
          :checked="sortAdditional"
          @change="$emit('update:sortAdditional', $event.target.checked)"
        />
        <span>Sort Additional Number</span>
      </label>
      <label>
        <input
          type="checkbox"
          :checked="colorful"
          @change="$emit('update:colorful', $event.target.checked)"
        />
        <span>Colorful</span>
      </label>
      <label>
        <input
          type="checkbox"
          :checked="onlyMatches"
          @change="$emit('update:onlyMatches', $event.target.checked)"
        />
        <span>Only matches</span>
      </label>
      <label>
        <input
          type="checkbox"
          :checked="onlyBigPayout"
          @change="$emit('update:onlyBigPayout', $event.target.checked)"
        />
        <span>{{ bigPayoutLabel }}</span>
      </label>
    </div>
  </div>
</template>

<style scoped>
.top { padding: 10px 16px 12px; background: #fff; border-bottom: 1px solid var(--border); }
.search-row { display: flex; gap: 12px; align-items: center; }
.search-row input {
  flex: 1;
  border: 1.5px solid #c7cdd6;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 16px;
  background: #fff;
  transition: border-color .15s;
}
.search-row input:focus { outline: none; border-color: var(--primary); }
.search-row input.invalid { border-color: var(--danger); }

.error {
  color: var(--danger);
  font-size: 13px;
  margin-top: 6px;
  text-align: center;
}

.toggles {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  column-gap: 20px;
  row-gap: 8px;
  margin-top: 12px;
  color: var(--primary);
  font-size: 15px;
}
.toggles label { display: inline-flex; align-items: center; gap: 6px; cursor: pointer; user-select: none; }
.toggles input[type="checkbox"] { width: 18px; height: 18px; accent-color: var(--primary); }
</style>
