<script setup lang="ts">
import { computed, watch } from 'vue'

import { coverSrc, newsApi } from '@/api/news'
import AppIcon from '@/components/ui/AppIcon.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import { fmtDateLong } from '@/utils/format'

const props = defineProps<{ slug: string }>()
const auth = useAuthStore()
const post = useAsync(() => newsApi.get(props.slug))

/** Текст хранится обычным текстом: пустая строка — новый абзац (без v-html — никакого HTML от автора) */
const paragraphs = computed(() =>
  (post.data.value?.body ?? '').split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean),
)
const cover = computed(() => (post.data.value ? coverSrc(post.data.value) : null))

watch(() => post.data.value?.title, (title) => {
  if (title) document.title = `${title} — bagdar.academy`
})
</script>

<template>
  <div class="container post-page">
    <RouterLink to="/news" class="back small"><AppIcon name="arrow-left" :size="14" /> {{ $t('news.back') }}</RouterLink>

    <StateBlock :loading="post.loading.value" :error="post.error.value" @retry="post.run">
      <article v-if="post.data.value" class="post">
        <header class="post__head">
          <div class="row post__meta">
            <span class="tag tag--teal">{{ $t(`news.categories.${post.data.value.category}`) }}</span>
            <time class="muted small" :datetime="post.data.value.published_at">{{ fmtDateLong(post.data.value.published_at) }}</time>
          </div>
          <h1>{{ post.data.value.title }}</h1>
          <p v-if="post.data.value.summary" class="post__lead">{{ post.data.value.summary }}</p>
        </header>

        <img v-if="cover" :src="cover" alt="" class="post__cover" />

        <div class="post__body">
          <p v-for="(p, i) in paragraphs" :key="i">{{ p }}</p>
        </div>

        <p v-if="post.data.value.author_name" class="muted small">{{ $t('news.author') }}: {{ post.data.value.author_name }}</p>
      </article>
    </StateBlock>

    <section v-if="!auth.isAuthenticated && post.data.value" class="band post-cta">
      <div>
        <h2>{{ $t('news.ctaTitle') }}</h2>
        <p class="muted">{{ $t('news.ctaText') }}</p>
      </div>
      <div class="row">
        <RouterLink to="/register" class="btn">{{ $t('public.register') }}</RouterLink>
        <RouterLink to="/login" class="btn btn--ghost">{{ $t('public.login') }}</RouterLink>
      </div>
    </section>
  </div>
</template>

<style scoped>
.post-page {
  max-width: 800px;
  display: grid;
  gap: var(--space-xl);
  padding-top: var(--space-xxl);
}
.back {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  justify-self: start;
}
.post {
  display: grid;
  gap: var(--space-xl);
}
.post__head {
  display: grid;
  gap: var(--space-sm);
}
.post__head h1 {
  margin: 0;
  font-size: var(--fs-h2);
  line-height: 1.15;
}
.post__meta {
  gap: var(--space-xs);
}
.post__lead {
  margin: 0;
  font-size: var(--fs-subtitle);
  line-height: 1.55;
  color: var(--text-secondary);
}
.post__cover {
  width: 100%;
  border-radius: var(--radius-lg);
  aspect-ratio: 16 / 9;
  object-fit: cover;
}
.post__body p {
  margin: 0 0 var(--space-md);
  font-size: var(--fs-body-md);
  line-height: 1.7;
  color: var(--text-body);
}
.post-cta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-lg);
  flex-wrap: wrap;
}
.post-cta h2 {
  margin: 0 0 4px;
  font-size: var(--fs-h4);
}
.post-cta p {
  margin: 0;
}
@media (max-width: 640px) {
  .post__head h1 {
    font-size: var(--fs-h3);
  }
}
</style>
