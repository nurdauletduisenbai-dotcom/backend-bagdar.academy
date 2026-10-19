import type { Role } from '@/types/api'

export interface NavItem {
  to: string
  label: string
  /** Кому показывать пункт. Пусто — всем авторизованным */
  roles?: Role[]
}

/**
 * Верхнее меню (вайрфрейм 1a): не больше 5 пунктов — главные задачи роли.
 * Набор выбирается по «старшей» роли в текущей организации.
 */
const topByRole: Record<Role, NavItem[]> = {
  admin: [
    { to: '/', label: 'Главная' },
    { to: '/admin', label: 'Сводка' },
    { to: '/teach/courses', label: 'Курсы' },
    { to: '/admin/members', label: 'Участники' },
    { to: '/admin/orders', label: 'Оплаты' },
  ],
  teacher: [
    { to: '/', label: 'Главная' },
    { to: '/teach/courses', label: 'Мои курсы' },
    { to: '/schedule', label: 'Расписание' },
    { to: '/teach/submissions', label: 'Проверка' },
    { to: '/teach/questions', label: 'Банк вопросов' },
  ],
  curator: [
    { to: '/', label: 'Главная' },
    { to: '/teach/courses', label: 'Курсы' },
    { to: '/schedule', label: 'Расписание' },
    { to: '/admin/members', label: 'Ученики' },
  ],
  parent: [
    { to: '/', label: 'Главная' },
    { to: '/children', label: 'Мои дети' },
    { to: '/schedule', label: 'Расписание' },
    { to: '/catalog', label: 'Курсы' },
  ],
  student: [
    { to: '/', label: 'Главная' },
    { to: '/my-courses', label: 'Курсы' },
    { to: '/schedule', label: 'Расписание' },
    { to: '/assignments', label: 'Задания' },
    { to: '/progress', label: 'Прогресс' },
  ],
}

const ROLE_PRIORITY: Role[] = ['admin', 'teacher', 'curator', 'parent', 'student']

/** Все разделы — для меню пользователя («остальное в профиле») */
export const allItems: NavItem[] = [
  { to: '/catalog', label: 'Каталог курсов' },
  { to: '/my-courses', label: 'Мои курсы', roles: ['student'] },
  { to: '/assignments', label: 'Задания', roles: ['student', 'teacher', 'admin'] },
  { to: '/progress', label: 'Мой прогресс', roles: ['student'] },
  { to: '/children', label: 'Мои дети', roles: ['parent'] },
  { to: '/schedule', label: 'Расписание' },
  { to: '/announcements', label: 'Объявления' },
  { to: '/teach/courses', label: 'Курсы школы', roles: ['teacher', 'admin', 'curator'] },
  { to: '/teach/questions', label: 'Банк вопросов', roles: ['teacher', 'admin'] },
  { to: '/teach/submissions', label: 'Проверка работ', roles: ['teacher', 'admin'] },
  { to: '/admin', label: 'Сводка школы', roles: ['admin'] },
  { to: '/admin/members', label: 'Участники', roles: ['admin', 'teacher', 'curator'] },
  { to: '/admin/invites', label: 'Приглашения', roles: ['admin', 'teacher'] },
  { to: '/admin/orders', label: 'Заказы и оплаты', roles: ['admin'] },
  { to: '/admin/audit', label: 'Журнал аудита', roles: ['admin'] },
  { to: '/admin/settings', label: 'Настройки школы', roles: ['admin'] },
  { to: '/orders', label: 'Мои заказы', roles: ['student', 'parent'] },
]

export function topLinks(roles: Role[]): NavItem[] {
  const main = ROLE_PRIORITY.find((r) => roles.includes(r))
  return main ? topByRole[main] : [{ to: '/', label: 'Главная' }, { to: '/catalog', label: 'Курсы' }]
}

export function menuLinks(roles: Role[]): NavItem[] {
  const top = new Set(topLinks(roles).map((i) => i.to))
  return allItems.filter((i) => !top.has(i.to) && (!i.roles || i.roles.some((r) => roles.includes(r))))
}
