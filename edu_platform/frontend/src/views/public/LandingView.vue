<script setup lang="ts">
import { computed } from 'vue'

import { coursesApi } from '@/api/courses'
import { newsApi } from '@/api/news'
import CourseCard from '@/components/course/CourseCard.vue'
import PostCard from '@/components/news/PostCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'
import type { PlatformStats } from '@/types/api'

/** Публичная главная: что такое bagdar.academy, новости, курсы и путь к регистрации */
const news = useAsync(() => newsApi.list({ page_size: 4 }))
const stats = useAsync(() => newsApi.stats())
const courses = useAsync(() => coursesApi.list({ page: 1 }))

const featured = computed(() => news.data.value?.results[0] ?? null)
const latest = computed(() => news.data.value?.results.slice(1, 4) ?? [])
const topCourses = computed(() => courses.data.value?.results.slice(0, 3) ?? [])

const statKeys: (keyof PlatformStats)[] = ['courses', 'students', 'teachers', 'schools']

const audiences = [
  { key: 'Student', icon: 'play' },
  { key: 'Parent', icon: 'user' },
  { key: 'Teacher', icon: 'edit' },
  { key: 'School', icon: 'calendar' },
] as const
</script>

<template>
  <!-- Герой: тёмная teal-полоса, главный CTA — регистрация -->
  <section class="hero">
    <div class="container hero__inner">
      <div class="hero__copy">
        <div class="eyebrow">bagdar.academy</div>
        <h1 class="hero__title">{{ $t('landing.heroTitle') }}</h1>
        <p class="hero__text">{{ $t('landing.heroText') }}</p>
        <div class="row hero__actions">
          <RouterLink to="/register" class="btn btn--lg">{{ $t('landing.heroPrimary') }}</RouterLink>
          <RouterLink to="/login" class="btn btn--ghost btn--lg">{{ $t('landing.heroSecondary') }}</RouterLink>
        </div>
      </div>
      <dl v-if="stats.data.value" class="hero__stats">
        <div v-for="k in statKeys" :key="k" class="hero__stat">
          <dt class="stat">{{ stats.data.value[k] }}</dt>
          <dd>{{ $t(`landing.stats.${k}`) }}</dd>
        </div>
      </dl>
    </div>
  </section>

  <div class="container landing">
    <!-- О платформе: для кого -->
    <section id="about" class="section">
      <header class="section__head">
        <div class="eyebrow">{{ $t('landing.aboutEyebrow') }}</div>
        <h2>{{ $t('landing.aboutTitle') }}</h2>
        <p class="muted section__lead">{{ $t('landing.aboutText') }}</p>
      </header>
      <div class="audiences">
        <article v-for="a in audiences" :key="a.key" class="card audience">
          <span class="audience__icon"><AppIcon :name="a.icon" :size="20" /></span>
          <h3>{{ $t(`landing.audience${a.key}Title`) }}</h3>
          <p class="muted">{{ $t(`landing.audience${a.key}Text`) }}</p>
        </article>
      </div>
    </section>

    <!-- Новости -->
    <section id="news" class="section">
      <header class="section__head section__head--row">
        <div>
          <div class="eyebrow">{{ $t('landing.newsEyebrow') }}</div>
          <h2>{{ $t('landing.newsTitle') }}</h2>
        </div>
        <RouterLink to="/news" class="btn btn--text">{{ $t('landing.allNews') }} <AppIcon name="arrow-right" :size="14" /></RouterLink>
      </header>
      <StateBlock :loading="news.loading.value" :error="news.error.value" :empty="!featured"
                  :empty-text="$t('landing.emptyNews')" @retry="news.run">
        <div class="stack">
          <PostCard v-if="featured" :post="featured" featured />
          <div v-if="latest.length" class="grid news-grid">
            <PostCard v-for="p in latest" :key="p.id" :post="p" />
          </div>
        </div>
      </StateBlock>
    </section>

    <!-- Курсы из публичного каталога -->
    <section v-if="topCourses.length" id="courses" class="section">
      <header class="section__head section__head--row">
        <div>
          <div class="eyebrow">{{ $t('landing.coursesEyebrow') }}</div>
          <h2>{{ $t('landing.coursesTitle') }}</h2>
        </div>
        <span class="muted small">{{ $t('landing.coursesNote') }}</span>
      </header>
      <div class="grid">
        <CourseCard v-for="c in topCourses" :key="c.id" :course="c" />
      </div>
    </section>

    <!-- Как начать -->
    <section id="start" class="section">
      <header class="section__head">
        <div class="eyebrow">{{ $t('landing.stepsEyebrow') }}</div>
        <h2>{{ $t('landing.stepsTitle') }}</h2>
      </header>
      <ol class="steps">
        <li v-for="n in 3" :key="n" class="card card--subtle step">
          <span class="step__num">{{ n }}</span>
          <h3>{{ $t(`landing.step${n}Title`) }}</h3>
          <p class="muted">{{ $t(`landing.step${n}Text`) }}</p>
        </li>
      </ol>
    </section>

    <!-- Финальный призыв -->
    <section class="band cta">
      <div>
        <h2>{{ $t('landing.ctaTitle') }}</h2>
        <p class="muted">{{ $t('landing.ctaText') }}</p>
      </div>
      <div class="row cta__actions">
        <RouterLink to="/register" class="btn btn--lg">{{ $t('public.register') }}</RouterLink>
        <RouterLink to="/invite" class="btn btn--ghost btn--lg">{{ $t('auth.haveInvite') }}</RouterLink>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero {
  background: radial-gradient(120% 120% at 0% 0%, var(--teal-700) 0%, var(--teal-900) 65%);
  color: var(--text-on-dark);
  padding: var(--space-section) 0;
}
.hero__inner {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  gap: var(--space-section-sm);
  align-items: end;
}
.hero__copy {
  display: grid;
  gap: var(--space-lg);
}
.hero .eyebrow {
  color: var(--green-500);
}
.hero__title {
  margin: 0;
  font: 500 var(--fs-display-lg) / 1.08 var(--font-sans);
  letter-spacing: -1px;
  color: var(--text-on-dark);
  max-width: 14ch;
}
.hero__text {
  margin: 0;
  max-width: 560px;
  font-size: var(--fs-subtitle);
  line-height: 1.55;
  color: var(--text-on-dark-muted);
}
.hero__actions {
  flex-wrap: wrap;
  margin-top: var(--space-xs);
}
.hero .btn--ghost {
  color: var(--text-on-dark);
  border-color: rgba(255, 255, 255, 0.35);
}
.hero .btn--ghost:hover {
  border-color: var(--text-on-dark);
}
.hero__stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-md);
  margin: 0;
}
.hero__stat {
  padding: var(--space-lg);
  border: 1px solid var(--border-dark);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.04);
}
.hero__stat dt {
  color: var(--text-on-dark);
  font-size: var(--fs-h2);
}
.hero__stat dd {
  margin: 4px 0 0;
  color: var(--text-on-dark-muted);
  font-size: var(--fs-body-sm);
}

.landing {
  display: grid;
  gap: var(--space-section);
  padding-top: var(--space-section);
}
.section {
  display: grid;
  gap: var(--space-xl);
  scroll-margin-top: calc(var(--nav-height) + var(--space-md));
}
.section__head {
  display: grid;
  gap: var(--space-xs);
}
.section__head h2 {
  margin: 0;
}
.section__head--row {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: var(--space-md);
  flex-wrap: wrap;
}
.section__lead {
  max-width: 640px;
  margin: 0;
}

.audiences {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-md);
}
.audience {
  display: grid;
  gap: var(--space-sm);
  align-content: start;
}
.audience h3,
.audience p {
  margin: 0;
}
.audience__icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  background: var(--surface-feature);
  color: var(--green-dark);
}

.news-grid {
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}

.steps {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-md);
}
.step {
  display: grid;
  gap: var(--space-sm);
  align-content: start;
}
.step h3,
.step p {
  margin: 0;
}
.step__num {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--teal-900);
  color: var(--green-500);
  font: 600 var(--fs-body-sm) / 1 var(--font-sans);
}

.cta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-xl);
  flex-wrap: wrap;
  padding: var(--space-xxxl);
}
.cta h2 {
  margin: 0 0 var(--space-xs);
}
.cta p {
  margin: 0;
  max-width: 520px;
}
.cta__actions {
  flex-wrap: wrap;
}

@media (max-width: 1024px) {
  .hero__inner {
    grid-template-columns: 1fr;
    align-items: start;
  }
  .hero__stats {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
  .audiences {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 640px) {
  .hero {
    padding: var(--space-section-sm) 0;
  }
  .hero__title {
    font-size: var(--fs-h2);
  }
  .hero__text {
    font-size: var(--fs-body-md);
  }
  .hero__stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .hero__stat dt {
    font-size: var(--fs-h3);
  }
  .landing {
    gap: var(--space-section-sm);
    padding-top: var(--space-section-sm);
  }
  .audiences,
  .steps {
    grid-template-columns: 1fr;
  }
  .cta {
    padding: var(--space-xl);
  }
}
</style>
