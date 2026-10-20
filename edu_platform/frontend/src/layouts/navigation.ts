import type { Role } from '@/types/api'

export interface NavItem {
  to: string
  /** Ключ i18n (см. locales/*.ts → nav.*), не литеральный текст */
  labelKey: string
  /** Кому показывать пункт. Пусто — всем авторизованным */
  roles?: Role[]
}

/**
 * Верхнее меню (вайрфрейм 1a): не больше 5 пунктов — главные задачи роли.
 * Набор выбирается по «старшей» роли в текущей организации.
 */
const topByRole: Record<Role, NavItem[]> = {
  admin: [
    { to: '/', labelKey: 'nav.home' },
    { to: '/admin', labelKey: 'nav.summary' },
    { to: '/teach/courses', labelKey: 'nav.courses' },
    { to: '/admin/members', labelKey: 'nav.members' },
    { to: '/admin/orders', labelKey: 'nav.orders' },
  ],
  teacher: [
    { to: '/', labelKey: 'nav.home' },
    { to: '/teach/courses', labelKey: 'nav.myCourses' },
    { to: '/schedule', labelKey: 'nav.schedule' },
    { to: '/teach/submissions', labelKey: 'nav.submissions' },
    { to: '/teach/questions', labelKey: 'nav.questionBank' },
  ],
  curator: [
    { to: '/', labelKey: 'nav.home' },
    { to: '/teach/courses', labelKey: 'nav.courses' },
    { to: '/schedule', labelKey: 'nav.schedule' },
    { to: '/admin/members', labelKey: 'nav.students' },
  ],
  parent: [
    { to: '/', labelKey: 'nav.home' },
    { to: '/children', labelKey: 'nav.children' },
    { to: '/schedule', labelKey: 'nav.schedule' },
    { to: '/catalog', labelKey: 'nav.catalog' },
  ],
  student: [
    { to: '/', labelKey: 'nav.home' },
    { to: '/my-courses', labelKey: 'nav.catalog' },
    { to: '/schedule', labelKey: 'nav.schedule' },
    { to: '/assignments', labelKey: 'nav.assignments' },
    { to: '/progress', labelKey: 'nav.progress' },
  ],
}

const ROLE_PRIORITY: Role[] = ['admin', 'teacher', 'curator', 'parent', 'student']

/** Все разделы — для меню пользователя («остальное в профиле») */
export const allItems: NavItem[] = [
  { to: '/catalog', labelKey: 'nav.catalog' },
  { to: '/my-courses', labelKey: 'nav.myCourses', roles: ['student'] },
  { to: '/assignments', labelKey: 'nav.assignments', roles: ['student', 'teacher', 'admin'] },
  { to: '/progress', labelKey: 'nav.progress', roles: ['student'] },
  { to: '/children', labelKey: 'nav.children', roles: ['parent'] },
  { to: '/schedule', labelKey: 'nav.schedule' },
  { to: '/announcements', labelKey: 'nav.announcements' },
  { to: '/teach/courses', labelKey: 'nav.courses', roles: ['teacher', 'admin', 'curator'] },
  { to: '/teach/questions', labelKey: 'nav.questionBank', roles: ['teacher', 'admin'] },
  { to: '/teach/submissions', labelKey: 'nav.submissions', roles: ['teacher', 'admin'] },
  { to: '/admin', labelKey: 'nav.summary', roles: ['admin'] },
  { to: '/admin/members', labelKey: 'nav.members', roles: ['admin', 'teacher', 'curator'] },
  { to: '/admin/invites', labelKey: 'nav.invites', roles: ['admin', 'teacher'] },
  { to: '/admin/orders', labelKey: 'nav.orders', roles: ['admin'] },
  { to: '/admin/audit', labelKey: 'nav.audit', roles: ['admin'] },
  { to: '/admin/settings', labelKey: 'nav.settings', roles: ['admin'] },
  { to: '/orders', labelKey: 'nav.myOrders', roles: ['student', 'parent'] },
]

export function topLinks(roles: Role[]): NavItem[] {
  const main = ROLE_PRIORITY.find((r) => roles.includes(r))
  return main ? topByRole[main] : [{ to: '/', labelKey: 'nav.home' }, { to: '/catalog', labelKey: 'nav.catalog' }]
}

export function menuLinks(roles: Role[]): NavItem[] {
  const top = new Set(topLinks(roles).map((i) => i.to))
  return allItems.filter((i) => !top.has(i.to) && (!i.roles || i.roles.some((r) => roles.includes(r))))
}
