import type { Role } from '@/types/api'

export interface NavItem {
  to: string
  label: string
  /** Кому показывать пункт. Пусто — всем авторизованным */
  roles?: Role[]
}

export interface NavGroup {
  title: string
  items: NavItem[]
}

export const navigation: NavGroup[] = [
  {
    title: 'Главное',
    items: [
      { to: '/', label: 'Главная' },
      { to: '/catalog', label: 'Каталог курсов' },
      { to: '/my-courses', label: 'Мои курсы', roles: ['student'] },
      { to: '/schedule', label: 'Расписание' },
      { to: '/assignments', label: 'Задания', roles: ['student', 'teacher', 'admin'] },
      { to: '/announcements', label: 'Объявления' },
      { to: '/notifications', label: 'Уведомления' },
    ],
  },
  {
    title: 'Успеваемость',
    items: [
      { to: '/progress', label: 'Мой прогресс', roles: ['student'] },
      { to: '/children', label: 'Мои дети', roles: ['parent'] },
    ],
  },
  {
    title: 'Преподавание',
    items: [
      { to: '/teach/courses', label: 'Мои курсы (учитель)', roles: ['teacher', 'admin', 'curator'] },
      { to: '/teach/questions', label: 'Банк вопросов', roles: ['teacher', 'admin'] },
      { to: '/teach/submissions', label: 'Проверка работ', roles: ['teacher', 'admin'] },
    ],
  },
  {
    title: 'Администрирование',
    items: [
      { to: '/admin', label: 'Сводка', roles: ['admin'] },
      { to: '/admin/members', label: 'Участники', roles: ['admin', 'teacher', 'curator'] },
      { to: '/admin/invites', label: 'Приглашения', roles: ['admin', 'teacher'] },
      { to: '/admin/orders', label: 'Заказы и оплаты', roles: ['admin'] },
      { to: '/admin/audit', label: 'Журнал аудита', roles: ['admin'] },
      { to: '/admin/settings', label: 'Настройки школы', roles: ['admin'] },
    ],
  },
  {
    title: 'Аккаунт',
    items: [
      { to: '/orders', label: 'Мои заказы', roles: ['student', 'parent'] },
      { to: '/profile', label: 'Профиль и безопасность' },
    ],
  },
]
