<script setup lang="ts">
import { ref, watch } from 'vue'

import { newsApi } from '@/api/news'
import PostCard from '@/components/news/PostCard.vue'
import AppPager from '@/components/ui/AppPager.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'
import type { NewsCategory } from '@/types/api'

const categories: NewsCategory[] = ['news', 'article', 'event', 'update']
const category = ref<NewsCategory | undefined>()
const page = ref(1)

const list = useAsync(() => newsApi.list({ category: category.value, page: page.value, page_size: 12 }))

watch(category, () => {
  page.value = 1
  list.run()
})
watch(page, () => list.run())
</script>

<template>
  <div class="container news-page">
    <header class="news-page__head">
      <div class="eyebrow">bagdar.academy</div>
      <h1>{{ $t('news.title') }}</h1>
      <p class="muted">{{ $t('news.subtitle') }}</p>
    </header>

    <div class="pills" role="group">
      <button type="button" class="pill" :class="{ active: !category }" @click="category = undefined">{{ $t('news.all') }}</button>
      <button v-for="c in categories" :key="c" type="button" class="pill" :class="{ active: category === c }"
              @click="category = c">
        {{ $t(`news.categories.${c}`) }}
      </button>
    </div>

    <StateBlock :loading="list.loading.value" :error="list.error.value" :empty="!list.data.value?.results.length"
                :empty-text="$t('news.empty')" @retry="list.run">
      <div class="grid news-page__grid">
        <PostCard v-for="p in list.data.value?.results" :key="p.id" :post="p" />
      </div>
      <AppPager :page="page" :total-pages="list.data.value?.total_pages ?? 1" @change="page = $event" />
    </StateBlock>
  </div>
</template>

<style scoped>
.news-page {
  display: grid;
  gap: var(--space-xl);
  padding-top: var(--space-section-sm);
}
.news-page__head {
  display: grid;
  gap: var(--space-xs);
}
.news-page__head h1,
.news-page__head p {
  margin: 0;
}
.news-page__grid {
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}
</style>
