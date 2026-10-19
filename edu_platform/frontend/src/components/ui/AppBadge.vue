<script setup lang="ts">
defineProps<{ kind?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'green' }>()
</script>

<template>
  <span class="badge" :class="kind && kind !== 'default' ? `badge--${kind}` : ''"><slot /></span>
</template>
