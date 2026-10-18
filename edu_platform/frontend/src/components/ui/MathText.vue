<script setup lang="ts">
import 'katex/dist/katex.min.css'

import katex from 'katex'
import { computed } from 'vue'

/** Текст с формулами: $…$ — внутри строки, $$…$$ — отдельной строкой (KaTeX). */
const props = defineProps<{ text: string; block?: boolean }>()

const escape = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

const html = computed(() =>
  (props.text ?? '')
    .split(/(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$)/g)
    .map((part) => {
      const display = part.startsWith('$$') && part.endsWith('$$') && part.length > 4
      const inline = !display && part.startsWith('$') && part.endsWith('$') && part.length > 2
      if (!display && !inline) return escape(part)
      const tex = display ? part.slice(2, -2) : part.slice(1, -1)
      return katex.renderToString(tex, { displayMode: display, throwOnError: false })
    })
    .join(''),
)
</script>

<template>
  <!-- eslint-disable-next-line vue/no-v-html — KaTeX экранирует TeX, обычный текст экранируем сами -->
  <component :is="block ? 'div' : 'span'" class="math-text" v-html="html" />
</template>

<style scoped>
.math-text {
  white-space: pre-line;
}
</style>
