<script setup lang="ts">
import { computed, ref } from 'vue'

import { coursesApi } from '@/api/courses'
import { newsApi } from '@/api/news'
import CourseCard from '@/components/course/CourseCard.vue'
import ContactForm from '@/components/landing/ContactForm.vue'
import FaqList from '@/components/landing/FaqList.vue'
import HeroMockup from '@/components/landing/HeroMockup.vue'
import UntCountdown from '@/components/landing/UntCountdown.vue'
import PostCard from '@/components/news/PostCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'
import type { PlatformStats } from '@/types/api'

/**
 * Публичная главная. Структура — по разбору лендингов:
 *  JUZ40 — результат и таймер до ҰБТ, «всё на одной платформе», заявка менеджеру;
 *  Khan Academy — выбор роли в герое, цифры, «как это работает», вкладки по аудиториям, FAQ;
 *  Padlet — один главный CTA, «бесплатно и за минуту», показываем сам продукт.
 */
const news = useAsync(() => newsApi.list({ page_size: 4 }))
const stats = useAsync(() => newsApi.stats())
const courses = useAsync(() => coursesApi.list({ page: 1 }))

const featured = computed(() => news.data.value?.results[0] ?? null)
const latest = computed(() => news.data.value?.results.slice(1, 4) ?? [])
const topCourses = computed(() => courses.data.value?.results.slice(0, 3) ?? [])

const statKeys: (keyof PlatformStats)[] = ['courses', 'students', 'teachers', 'schools']

const roles = [
  { key: 'Student', icon: 'play', to: '/register?role=student' },
  { key: 'Parent', icon: 'user', to: '/register?role=parent' },
  { key: 'School', icon: 'edit', to: { path: '/', hash: '#contact' } },
] as const

const features = [
  { key: 'Tests', icon: 'check' },
  { key: 'Video', icon: 'play' },
  { key: 'Homework', icon: 'upload' },
  { key: 'Progress', icon: 'circle' },
  { key: 'Support', icon: 'user' },
  { key: 'Schedule', icon: 'bell' },
] as const

const audiences = [
  { key: 'Student', to: '/register?role=student' },
  { key: 'Parent', to: '/register?role=parent' },
  { key: 'Teacher', to: { path: '/', hash: '#contact' } },
  { key: 'School', to: { path: '/', hash: '#contact' } },
] as const
const tab = ref<(typeof audiences)[number]['key']>('Student')
const activeAudience = computed(() => audiences.find((a) => a.key === tab.value)!)
</script>

<template>
  <!-- 1. Герой: слоган, выбор роли (Khan), «бесплатно за минуту» (Padlet), интерфейс продукта -->
  <section class="hero">
    <div class="container hero__inner">
      <div class="hero__copy">
        <div class="eyebrow">{{ $t('landing.heroEyebrow') }}</div>
        <h1 class="hero__title">{{ $t('landing.heroTitle') }}</h1>
        <p class="hero__text">{{ $t('landing.heroText') }}</p>

        <div class="hero__roles">
          <span class="hero__roles-title">{{ $t('landing.roleTitle') }}</span>
          <div class="roles">
            <RouterLink v-for="r in roles" :key="r.key" :to="r.to" class="role">
              <span class="role__icon"><AppIcon :name="r.icon" :size="18" /></span>
              <span class="role__text">
                <strong>{{ $t(`landing.role${r.key}`) }}</strong>
                <small>{{ $t(`landing.role${r.key}Hint`) }}</small>
              </span>
              <AppIcon name="arrow-right" :size="16" class="role__arrow" />
            </RouterLink>
          </div>
          <p class="hero__note">
            {{ $t('landing.freeNote') }} {{ $t('landing.haveAccount') }}
            <RouterLink to="/login">{{ $t('public.login') }}</RouterLink>
          </p>
        </div>
      </div>
      <HeroMockup class="hero__mock" />
    </div>
  </section>

  <div class="container landing">
    <!-- 2. Цифры платформы (реальные, из API) + таймер до ҰБТ (JUZ40) -->
    <section class="proof">
      <dl v-if="stats.data.value" class="proof__stats">
        <div v-for="k in statKeys" :key="k" class="proof__stat">
          <dt class="stat">{{ stats.data.value[k] }}</dt>
          <dd class="muted small">{{ $t(`landing.stats.${k}`) }}</dd>
        </div>
      </dl>
      <UntCountdown />
    </section>

    <!-- 3. Всё на одной платформе (JUZ40) -->
    <section id="about" class="section">
      <header class="section__head">
        <div class="eyebrow">{{ $t('landing.featuresEyebrow') }}</div>
        <h2>{{ $t('landing.featuresTitle') }}</h2>
      </header>
      <div class="features">
        <article v-for="f in features" :key="f.key" class="feature">
          <span class="feature__icon"><AppIcon :name="f.icon" :size="20" /></span>
          <h3>{{ $t(`landing.feat${f.key}Title`) }}</h3>
          <p class="muted">{{ $t(`landing.feat${f.key}Text`) }}</p>
        </article>
      </div>
    </section>

    <!-- 4. Как проходит обучение (Khan) -->
    <section class="band how">
      <header class="section__head">
        <div class="eyebrow">{{ $t('landing.howEyebrow') }}</div>
        <h2>{{ $t('landing.howTitle') }}</h2>
      </header>
      <ol class="how__steps">
        <li v-for="n in 3" :key="n" class="how__step">
          <span class="how__num">{{ n }}</span>
          <div>
            <h3>{{ $t(`landing.how${n}Title`) }}</h3>
            <p class="muted">{{ $t(`landing.how${n}Text`) }}</p>
          </div>
        </li>
      </ol>
    </section>

    <!-- 5. Для кого: вкладки по аудиториям (Khan) -->
    <section class="section">
      <header class="section__head">
        <div class="eyebrow">{{ $t('landing.audEyebrow') }}</div>
        <h2>{{ $t('landing.audTitle') }}</h2>
      </header>
      <div class="tabs" role="tablist">
        <button v-for="a in audiences" :key="a.key" type="button" role="tab" :aria-selected="tab === a.key"
                :class="{ active: tab === a.key }" @click="tab = a.key">
          {{ $t(`landing.aud${a.key}Tab`) }}
        </button>
      </div>
      <div class="card audience" role="tabpanel">
        <div class="audience__copy">
          <h3>{{ $t(`landing.aud${tab}Title`) }}</h3>
          <p class="muted">{{ $t(`landing.aud${tab}Text`) }}</p>
          <RouterLink :to="activeAudience.to" class="btn">{{ $t(`landing.aud${tab}Cta`) }}</RouterLink>
        </div>
        <ul class="audience__list">
          <li v-for="b in 4" :key="b"><AppIcon name="check" :size="16" /> {{ $t(`landing.aud${tab}B${b}`) }}</li>
        </ul>
      </div>
    </section>

    <!-- 6. Курсы из публичного каталога (аналог тарифов JUZ40: цена видна сразу) -->
    <section v-if="topCourses.length" id="courses" class="section">
      <header class="section__head section__head--row">
        <div>
          <div class="eyebrow">{{ $t('landing.coursesEyebrow') }}</div>
          <h2>{{ $t('landing.coursesTitle') }}</h2>
        </div>
        <span class="muted small">{{ $t('landing.coursesNote') }}</span>
      </header>
      <div class="courses-grid">
        <CourseCard v-for="c in topCourses" :key="c.id" :course="c" />
      </div>
    </section>

    <!-- 7. Новости -->
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

    <!-- 8. FAQ (Khan) + заявка менеджеру (JUZ40) -->
    <section class="split-2">
      <div id="faq" class="section">
        <header class="section__head">
          <div class="eyebrow">{{ $t('landing.faqEyebrow') }}</div>
          <h2>{{ $t('landing.faqTitle') }}</h2>
        </header>
        <FaqList />
      </div>
      <div id="contact" class="card card--subtle section contact">
        <header class="section__head">
          <div class="eyebrow">{{ $t('landing.contactEyebrow') }}</div>
          <h2>{{ $t('landing.contactTitle') }}</h2>
          <p class="muted">{{ $t('landing.contactText') }}</p>
        </header>
        <ContactForm />
      </div>
    </section>

    <!-- 9. Финальный призыв -->
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
/* ---------- Герой ---------- */
.hero {
  background: radial-gradient(120% 120% at 0% 0%, var(--teal-700) 0%, var(--teal-900) 65%);
  color: var(--text-on-dark);
  padding: var(--space-section) 0;
  overflow: hidden;
}
.hero__inner {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  gap: var(--space-section-sm);
  align-items: center;
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
  font: 500 var(--fs-display-lg) / 1.06 var(--font-sans);
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
.hero__roles {
  display: grid;
  gap: var(--space-sm);
  margin-top: var(--space-xs);
}
.hero__roles-title {
  font: 600 var(--fs-body-sm) / 1.2 var(--font-sans);
}
.roles {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-sm);
}
.role {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-dark);
  color: var(--text-on-dark);
  text-decoration: none;
  transition: background 0.15s, border-color 0.15s;
}
.role:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: var(--green-500);
  text-decoration: none;
}
.role__icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--green-500);
  color: var(--teal-900);
}
.role__text {
  display: grid;
  min-width: 0;
}
.role__text strong {
  font: 600 var(--fs-body-sm) / 1.25 var(--font-sans);
}
.role__text small {
  font-size: var(--fs-micro);
  color: var(--text-on-dark-muted);
}
.role__arrow {
  margin-left: auto;
  flex-shrink: 0;
  color: var(--text-on-dark-muted);
}
.hero__note {
  margin: 0;
  font-size: var(--fs-body-sm);
  color: var(--text-on-dark-muted);
}
.hero__note a {
  color: var(--green-500);
}

/* ---------- Секции ---------- */
.landing {
  display: grid;
  gap: var(--space-section);
  padding-top: var(--space-xxl);
}
.section {
  display: grid;
  gap: var(--space-xl);
  align-content: start;
  scroll-margin-top: calc(var(--nav-height) + var(--space-md));
}
.section__head {
  display: grid;
  gap: var(--space-xs);
}
.section__head h2,
.section__head p {
  margin: 0;
}
.section__head--row {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: var(--space-md);
  flex-wrap: wrap;
}

/* Цифры + таймер */
.proof {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--space-md);
  align-items: stretch;
}
.proof__stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 0;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
}
.proof__stat {
  padding: var(--space-lg) var(--space-xl);
}
.proof__stat + .proof__stat {
  border-left: 1px solid var(--border-default);
}
.proof__stat dd {
  margin: 4px 0 0;
}

/* Возможности */
.features {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-xxl) var(--space-xl);
}
.feature {
  display: grid;
  gap: var(--space-xs);
  align-content: start;
}
.feature h3,
.feature p {
  margin: 0;
}
.feature h3 {
  font-size: var(--fs-h5);
}
.feature__icon {
  width: 44px;
  height: 44px;
  margin-bottom: var(--space-xs);
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  background: var(--surface-feature);
  color: var(--green-dark);
}

/* Как проходит обучение */
.how {
  display: grid;
  gap: var(--space-xl);
  padding: var(--space-xxxl);
}
.how__steps {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-xl);
  counter-reset: none;
}
.how__step {
  display: flex;
  gap: var(--space-md);
  align-items: flex-start;
}
.how__step h3 {
  margin: 0 0 4px;
}
.how__step p {
  margin: 0;
}
.how__num {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--green-500);
  color: var(--teal-900);
  font: 600 var(--fs-body-md) / 1 var(--font-sans);
}

/* Аудитории */
.audience {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--space-xxl);
  align-items: center;
  padding: var(--space-xxl);
  margin-top: calc(-1 * var(--space-xl));
}
.audience__copy {
  display: grid;
  gap: var(--space-md);
  justify-items: start;
}
.audience__copy h3,
.audience__copy p {
  margin: 0;
}
.audience__copy h3 {
  font-size: var(--fs-h3);
  line-height: 1.2;
}
.audience__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: var(--space-sm);
}
.audience__list li {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  background: var(--surface-subtle);
  font-weight: 500;
}
.audience__list :deep(svg) {
  color: var(--green-dark);
  flex-shrink: 0;
}

.news-grid {
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}
.courses-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-md);
}

/* FAQ + заявка */
.split-2 {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
  gap: var(--space-section-sm);
  align-items: start;
}
.contact {
  padding: var(--space-xxl);
}

/* Финальный CTA */
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

@media (max-width: 1100px) {
  .hero__inner {
    grid-template-columns: 1fr;
  }
  .hero__mock {
    max-width: 520px;
  }
  .proof {
    grid-template-columns: 1fr;
  }
  .features {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .split-2 {
    grid-template-columns: 1fr;
  }
  .courses-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 760px) {
  .roles {
    grid-template-columns: 1fr;
  }
  .proof__stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .proof__stat:nth-child(3) {
    border-left: 0;
  }
  .proof__stat:nth-child(n + 3) {
    border-top: 1px solid var(--border-default);
  }
  .how__steps,
  .audience {
    grid-template-columns: 1fr;
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
  .hero__mock {
    display: none;
  }
  .landing {
    gap: var(--space-section-sm);
  }
  .features,
  .courses-grid {
    grid-template-columns: 1fr;
  }
  .how,
  .audience,
  .contact,
  .cta {
    padding: var(--space-xl);
  }
}
</style>
