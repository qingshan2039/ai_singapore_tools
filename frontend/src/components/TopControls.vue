<script setup>
defineProps({
  sortAdditional: Boolean,
  colorful: Boolean,
})
defineEmits(['update:sortAdditional', 'update:colorful', 'scan'])
</script>

<template>
  <div class="top">
    <div class="search-row">
      <input type="text" placeholder="" aria-label="Search" />
      <button class="scan" @click="$emit('scan')">Scan</button>
    </div>
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
}
.scan { background: none; border: none; color: var(--primary); font-size: 18px; font-weight: 500; cursor: pointer; padding: 0 4px; }

.toggles { display: flex; justify-content: center; gap: 28px; margin-top: 12px; color: var(--primary); font-size: 17px; }
.toggles label { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; user-select: none; }
.toggles input[type="checkbox"] { width: 20px; height: 20px; accent-color: var(--primary); }
</style>
