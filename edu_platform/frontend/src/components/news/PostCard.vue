<script setup lang="ts">
import { computed } from 'vue'

import { coverSrc } from '@/api/news'
import AppIcon from '@/components/ui/AppIcon.vue'
import type { NewsCategory, NewsPost } from '@/types/api'
import { fmtDateLong } from '@/utils/format'

/** Карточка публикации. `featured` — крупная горизонтальная (закреплённая новость на главной) */
const props = defineProps<{ post: NewsPost; featured?: boolean }>()

const tone: Record<NewsCategory, string> = {
  news: 'tag--teal',
  article: 'tag--blue',
  event: 'tag--orange',
  update: 'tag--purple',
}
const cover = computed(() => coverSrc(props.post))
</script>

<template>
  <RouterLink :to="`/news/${post.slug}`" class="card card--link post-card" :class="{ 'post-card--featured': featured }">
    <div class="post-card__cover">
      <img v-if="cover" :src="cover" alt="" loading="lazy" />
      <span v-else class="post-card__mark" aria-hidden="true">bagdar<span>.</span></span>
    </div>
    <div class="post-card__body">
      <div class="row post-card__meta">
        <span class="tag" :class="tone[post.category]">{{ $t(`news.categories.${post.category}`) }}</span>
        <span v-if="post.is_pinned" class="badge badge--green">{{ $t('news.pinned') }}</span>
        <time class="muted small" :datetime="post.published_at">{{ fmtDateLong(post.published_at) }}</time>
      </div>
      <h3 class="post-card__title">{{ post.title }}</h3>
      <p class="post-card__summary">{{ post.summary }}</p>
      <span class="post-card__more">{{ $t('news.readMore') }} <AppIcon name="arrow-right" :size="14" /></span>
    </div>
  </RouterLink>
</template>

<style scoped>
.post-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  height: 100%;
  color: inherit;
}
.post-card__cover {
  aspect-ratio: 16 / 9;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: radial-gradient(120% 120% at 0% 0%, var(--teal-700) 0%, var(--teal-900) 70%);
  display: grid;
  place-items: center;
}
.post-card__cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.post-card__mark {
  font: 600 22px / 1 var(--font-sans);
  letter-spacing: -0.5px;
  color: var(--text-on-dark-muted);
}
.post-card__mark span {
  color: var(--green-500);
}
.post-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  flex: 1;
}
.post-card__meta {
  flex-wrap: wrap;
  gap: var(--space-xs);
}
.post-card__title {
  margin: 0;
  font: 500 var(--fs-h5) / 1.35 var(--font-sans);
  color: var(--text-strong);
}
.post-card__summary {
  margin: 0;
  color: var(--text-secondary);
  font-size: var(--fs-body-sm);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.post-card__more {
  margin-top: auto;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--text-link);
  font: 500 var(--fs-body-sm) / 1 var(--font-sans);
}

.post-card--featured {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  gap: var(--space-xl);
  align-items: stretch;
}
.post-card--featured .post-card__cover {
  aspect-ratio: auto;
  min-height: 260px;
}
.post-card--featured .post-card__mark {
  font-size: 40px;
}
.post-card--featured .post-card__body {
  justify-content: center;
  padding: var(--space-md) 0;
}
.post-card--featured .post-card__title {
  font-size: var(--fs-h3);
  line-height: 1.2;
  letter-spacing: -0.3px;
}
.post-card--featured .post-card__summary {
  font-size: var(--fs-body-md);
  -webkit-line-clamp: 4;
}
.post-card--featured .post-card__more {
  margin-top: var(--space-sm);
}
@media (max-width: 760px) {
  .post-card--featured {
    grid-template-columns: 1fr;
  }
  .post-card--featured .post-card__cover {
    min-height: 0;
    aspect-ratio: 16 / 9;
  }
  .post-card--featured .post-card__title {
    font-size: var(--fs-h4);
  }
}
</style>
