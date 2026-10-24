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

const LETTERS = 'ABCDEFGHIJ'
const ids = computed(() => (Array.isArray(props.selected) ? props.selected : []))
const pairs = computed(() => (Array.isArray(props.selected) ? {} : props.selected))

function toggle(id: number) {
  if (props.disabled) return
  if (props.question.type === 'single') return emit('update:selected', [id])
  const next = ids.value.includes(id) ? ids.value.filter((x) => x !== id) : [...ids.value, id]
  emit('update:selected', next)
}

function setPair(optionId: number, target: string) {
  emit('update:selected', { ...pairs.value, [String(optionId)]: target })
}
</script>

<template>
  <div class="answer">
    <template v-if="question.type === 'single' || question.type === 'multi'">
      <div class="choices">
        <button v-for="(opt, i) in question.options" :key="opt.id" type="button" class="choice"
                :class="{ selected: ids.includes(opt.id) }" :aria-pressed="ids.includes(opt.id)" :disabled="disabled"
                @click="toggle(opt.id)">
          <span class="choice__letter">{{ LETTERS[i] }}</span>
          <MathText :text="opt.text" />
        </button>
      </div>
      <span v-if="question.type === 'multi'" class="muted small">Можно выбрать несколько вариантов.</span>
    </template>

    <template v-else-if="question.type === 'match'">
      <div v-for="opt in question.options" :key="opt.id" class="match">
        <MathText :text="opt.text" class="match__left" />
        <select :value="pairs[String(opt.id)] ?? ''" :disabled="disabled"
                @change="setPair(opt.id, ($event.target as HTMLSelectElement).value)">
          <option value="">— выберите —</option>
          <option v-for="t in question.match_targets ?? []" :key="t" :value="t">{{ t }}</option>
        </select>
      </div>
    </template>

    <input v-else-if="question.type === 'short' || question.type === 'number'" :value="text" :disabled="disabled"
           :inputmode="question.type === 'number' ? 'decimal' : 'text'"
           :placeholder="question.type === 'number' ? 'Введите число' : 'Ваш ответ'" class="short"
           @input="emit('update:text', ($event.target as HTMLInputElement).value)" />

    <textarea v-else :value="text" :disabled="disabled" placeholder="Развёрнутый ответ — проверит учитель"
              @input="emit('update:text', ($event.target as HTMLTextAreaElement).value)" />
  </div>
</template>

<style scoped>
.answer {
  display: grid;
  gap: var(--space-sm);
}
.choices {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-sm);
}
.choice {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  min-height: 56px;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  background: var(--canvas);
  color: var(--text-strong);
  font: 400 var(--fs-body-md) / var(--lh-body-md) var(--font-sans);
  text-align: left;
  cursor: pointer;
  transition: border-color var(--dur-fast) var(--ease-standard), background var(--dur-fast) var(--ease-standard);
}
.choice:hover {
  border-color: var(--text-strong);
}
.choice.selected {
  border: 2px solid var(--green-dark);
  background: var(--surface-feature);
  padding: calc(var(--space-sm) - 1px) calc(var(--space-md) - 1px);
}
.choice__letter {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--surface-soft);
  font: 600 var(--fs-caption) / 1 var(--font-sans);
}
.choice.selected .choice__letter {
  background: var(--green-500);
  color: var(--teal-900);
}
.match {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(180px, 280px);
  gap: var(--space-sm);
  align-items: center;
}
.short {
  max-width: 360px;
}
</style>
