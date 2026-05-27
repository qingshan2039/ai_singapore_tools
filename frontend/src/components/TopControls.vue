<script setup>
defineProps({
  search: { type: String, default: '' },
  searchError: { type: String, default: '' },
  sortAdditional: Boolean,
  colorful: Boolean,
})
defineEmits(['update:search', 'update:sortAdditional', 'update:colorful'])
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

.toggles { display: flex; justify-content: center; gap: 28px; margin-top: 12px; color: var(--primary); font-size: 17px; }
.toggles label { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; user-select: none; }
.toggles input[type="checkbox"] { width: 20px; height: 20px; accent-color: var(--primary); }
</style>
