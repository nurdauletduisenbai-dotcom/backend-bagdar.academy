import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/stores/toast'
import type { Role } from '@/types/api'

declare module 'vue-router' {
  interface RouteMeta {
    /** Страница без входа (логин, регистрация...) */
    public?: boolean
    /** Только для гостей: авторизованного перекинет на главную */
    guestOnly?: boolean
    /** Кому доступна страница (роль в текущей организации) */
    roles?: Role[]
    title?: string
  }
}

const STAFF: Role[] = ['admin', 'teacher', 'curator']
const TEACHERS: Role[] = ['admin', 'teacher']

const routes: RouteRecordRaw[] = [
  // ---------- Публичные ----------
  { path: '/login', name: 'login', component: () => import('@/views/auth/LoginView.vue'), meta: { public: true, guestOnly: true, title: 'Вход' } },
  { path: '/register', name: 'register', component: () => import('@/views/auth/RegisterView.vue'), meta: { public: true, guestOnly: true, title: 'Регистрация' } },
  { path: '/invite', name: 'invite', component: () => import('@/views/auth/InviteRegisterView.vue'), meta: { public: true, guestOnly: true, title: 'Приглашение' } },
  { path: '/forgot-password', name: 'forgot-password', component: () => import('@/views/auth/ForgotPasswordView.vue'), meta: { public: true, guestOnly: true, title: 'Восстановление пароля' } },
  { path: '/reset-password', name: 'reset-password', component: () => import('@/views/auth/ResetPasswordView.vue'), meta: { public: true, title: 'Новый пароль' } },
  { path: '/verify-email', name: 'verify-email', component: () => import('@/views/auth/VerifyEmailView.vue'), meta: { public: true, title: 'Подтверждение email' } },

  // ---------- Публичный сайт: главная с новостями (вошедших главная перекидывает в кабинет /home) ----------
  {
    path: '/',
    component: () => import('@/layouts/PublicLayout.vue'),
    children: [
      { path: '', name: 'landing', component: () => import('@/views/public/LandingView.vue'), meta: { public: true, guestOnly: true, title: 'bagdar.academy' } },
      { path: 'news', name: 'news', component: () => import('@/views/public/NewsListView.vue'), meta: { public: true, title: 'Новости' } },
      { path: 'news/:slug', name: 'news-post', component: () => import('@/views/public/PostView.vue'), props: true, meta: { public: true, title: 'Новости' } },
    ],
  },

  // ---------- Приложение ----------
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    children: [
      { path: 'home', name: 'home', component: () => import('@/views/HomeView.vue'), meta: { title: 'Главная' } },
      { path: 'catalog', name: 'catalog', component: () => import('@/views/CoursesView.vue'), meta: { title: 'Каталог' } },
      { path: 'my-courses', name: 'my-courses', component: () => import('@/views/courses/MyCoursesView.vue'), meta: { title: 'Мои курсы' } },
      { path: 'courses/:id', name: 'course', component: () => import('@/views/courses/CourseView.vue'), props: true, meta: { title: 'Курс' } },
      { path: 'lessons/:id', name: 'lesson', component: () => import('@/views/courses/LessonView.vue'), props: true, meta: { title: 'Урок' } },

      { path: 'tests/:id/take', name: 'test-take', component: () => import('@/views/tests/TestTakeView.vue'), props: true, meta: { title: 'Тест' } },
      { path: 'attempts/:id', name: 'attempt', component: () => import('@/views/tests/AttemptResultView.vue'), props: true, meta: { title: 'Результат' } },

      { path: 'assignments', name: 'assignments', component: () => import('@/views/assignments/AssignmentsView.vue'), meta: { title: 'Задания' } },
      { path: 'assignments/:id', name: 'assignment', component: () => import('@/views/assignments/AssignmentView.vue'), props: true, meta: { title: 'Задание' } },

      { path: 'schedule', name: 'schedule', component: () => import('@/views/ScheduleView.vue'), meta: { title: 'Расписание' } },
      { path: 'notifications', name: 'notifications', component: () => import('@/views/NotificationsView.vue'), meta: { title: 'Уведомления' } },
      { path: 'announcements', name: 'announcements', component: () => import('@/views/AnnouncementsView.vue'), meta: { title: 'Объявления' } },

      { path: 'progress', name: 'progress', component: () => import('@/views/progress/MyProgressView.vue'), meta: { title: 'Прогресс' } },
      { path: 'progress/courses/:courseId', name: 'course-report', component: () => import('@/views/progress/CourseReportView.vue'), props: true, meta: { title: 'Отчёт по курсу' } },
      { path: 'children', name: 'children', component: () => import('@/views/progress/ChildrenView.vue'), meta: { roles: ['parent'], title: 'Мои дети' } },
      { path: 'orders', name: 'orders', component: () => import('@/views/OrdersView.vue'), meta: { title: 'Мои заказы' } },
      { path: 'profile', name: 'profile', component: () => import('@/views/ProfileView.vue'), meta: { title: 'Профиль' } },

      // ---------- Преподавание ----------
      { path: 'teach/courses', name: 'teach-courses', component: () => import('@/views/teach/TeachCoursesView.vue'), meta: { roles: STAFF, title: 'Курсы' } },
      { path: 'teach/courses/:id', name: 'course-editor', component: () => import('@/views/teach/CourseEditorView.vue'), props: true, meta: { roles: STAFF, title: 'Редактор курса' } },
      { path: 'teach/lessons/:id', name: 'lesson-editor', component: () => import('@/views/teach/LessonEditorView.vue'), props: true, meta: { roles: TEACHERS, title: 'Редактор урока' } },
      { path: 'teach/tests/:id', name: 'test-editor', component: () => import('@/views/teach/TestEditorView.vue'), props: true, meta: { roles: STAFF, title: 'Редактор теста' } },
      { path: 'teach/questions', name: 'question-bank', component: () => import('@/views/teach/QuestionBankView.vue'), meta: { roles: TEACHERS, title: 'Банк вопросов' } },
      { path: 'teach/submissions', name: 'submissions', component: () => import('@/views/teach/SubmissionsView.vue'), meta: { roles: TEACHERS, title: 'Проверка работ' } },

      // ---------- Администрирование ----------
      { path: 'admin', name: 'admin', component: () => import('@/views/admin/AdminDashboardView.vue'), meta: { roles: ['admin'], title: 'Сводка' } },
      { path: 'admin/members', name: 'members', component: () => import('@/views/admin/MembersView.vue'), meta: { roles: STAFF, title: 'Участники' } },
      { path: 'admin/invites', name: 'invites', component: () => import('@/views/admin/InvitesView.vue'), meta: { roles: TEACHERS, title: 'Приглашения' } },
      { path: 'admin/orders', name: 'admin-orders', component: () => import('@/views/OrdersView.vue'), props: { admin: true }, meta: { roles: ['admin'], title: 'Заказы' } },
      { path: 'admin/audit', name: 'audit', component: () => import('@/views/admin/AuditView.vue'), meta: { roles: ['admin'], title: 'Аудит' } },
      { path: 'admin/settings', name: 'org-settings', component: () => import('@/views/admin/OrgSettingsView.vue'), meta: { roles: ['admin'], title: 'Настройки' } },
    ],
  },

  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFoundView.vue'), meta: { public: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  // Якоря главной (#about, #courses…) — плавная прокрутка; отступ задаёт scroll-margin-top секции
  scrollBehavior: (to) => (to.hash ? { el: to.hash, behavior: 'smooth' } : { top: 0 }),
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login', query: { next: to.fullPath } }
  }
  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: 'home' }
  }
  if (to.meta.roles && !auth.hasRole(...to.meta.roles)) {
    useToast().error('Эта страница недоступна для вашей роли в текущей организации.')
    return { name: 'home' }
  }
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} — EduPlatform` : 'EduPlatform'
})

export default router
