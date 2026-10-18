<script setup lang="ts">
import { computed } from 'vue'

import MathText from '@/components/ui/MathText.vue'
import type { AttemptQuestion } from '@/types/api'

/** Поле ответа для одного вопроса теста. Значение — то, что уходит в API. */
const props = defineProps<{
  question: AttemptQuestion
  selected: number[] | Record<string, string>
  text: string
  disabled?: boolean
}>()
const emit = defineEmits<{
  'update:selected': [value: number[] | Record<string, string>]
  'update:text': [value: string]
}>()

const ids = computed(() => (Array.isArray(props.selected) ? props.selected : []))
const pairs = computed(() => (Array.isArray(props.selected) ? {} : props.selected))

function toggle(id: number) {
  if (props.question.type === 'single') return emit('update:selected', [id])
  const next = ids.value.includes(id) ? ids.value.filter((x) => x !== id) : [...ids.value, id]
  emit('update:selected', next)
}

function setPair(optionId: number, target: string) {
  emit('update:selected', { ...pairs.value, [String(optionId)]: target })
}
</script>

<template>
  <div class="stack" style="gap: 8px">
    <template v-if="question.type === 'single' || question.type === 'multi'">
      <label v-for="opt in question.options" :key="opt.id" class="inline option">
        <input :type="question.type === 'single' ? 'radio' : 'checkbox'" :name="`q${question.id}`" :disabled="disabled"
               :checked="ids.includes(opt.id)" @change="toggle(opt.id)" />
        <MathText :text="opt.text" />
      </label>
      <span v-if="question.type === 'multi'" class="muted small">Можно выбрать несколько вариантов.</span>
    </template>

    <template v-else-if="question.type === 'match'">
      <div v-for="opt in question.options" :key="opt.id" class="row">
        <MathText :text="opt.text" style="min-width: 160px" />
        <select :value="pairs[String(opt.id)] ?? ''" :disabled="disabled" style="max-width: 260px"
                @change="setPair(opt.id, ($event.target as HTMLSelectElement).value)">
          <option value="">— выберите —</option>
          <option v-for="t in question.match_targets ?? []" :key="t" :value="t">{{ t }}</option>
        </select>
      </div>
    </template>

    <input v-else-if="question.type === 'short' || question.type === 'number'" :value="text" :disabled="disabled"
           :inputmode="question.type === 'number' ? 'decimal' : 'text'"
           :placeholder="question.type === 'number' ? 'Число' : 'Ответ'" style="max-width: 320px"
           @input="emit('update:text', ($event.target as HTMLInputElement).value)" />

    <textarea v-else :value="text" :disabled="disabled" placeholder="Развёрнутый ответ (проверит учитель)"
              @input="emit('update:text', ($event.target as HTMLTextAreaElement).value)" />
  </div>
</template>

<style scoped>
.option {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
}
</style>
