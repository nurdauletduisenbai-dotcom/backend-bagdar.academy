<script setup lang="ts">
defineProps<{ kind?: 'default' | 'success' | 'warning' | 'danger' | 'info' }>()
</script>

<template>
  <span class="badge" :class="kind ? `badge--${kind}` : ''"><slot /></span>
</template>
