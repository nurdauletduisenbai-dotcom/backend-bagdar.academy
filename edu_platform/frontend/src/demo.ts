/**
 * Демо-аккаунты для локальной проверки (создаются `make seed`).
 * Кнопки быстрого входа показываются, только если VITE_SHOW_DEMO_ACCOUNTS !== 'false'.
 */
export interface DemoAccount {
  role: string
  email: string
  password: string
  note: string
}

export const demoAccounts: DemoAccount[] = [
  { role: 'Администратор', email: 'admin@fizmat.kz', password: 'AdminPassword123!', note: 'участники, оплаты, аудит, сводка' },
  { role: 'Учитель', email: 'teacher@fizmat.kz', password: 'TeacherPassword123!', note: 'курсы, тесты, проверка работ, посещаемость' },
  { role: 'Куратор', email: 'curator@fizmat.kz', password: 'CuratorPassword123!', note: 'просмотр курсов и прогресса учеников' },
  { role: 'Ученик', email: 'student1@fizmat.kz', password: 'StudentPassword123!', note: 'уроки, тесты, задания (записан на курсы)' },
  { role: 'Ученик 2', email: 'student2@fizmat.kz', password: 'StudentPassword123!', note: 'не записан на платный курс — можно купить' },
  { role: 'Родитель', email: 'parent@fizmat.kz', password: 'ParentPassword123!', note: 'прогресс ребёнка (student1)' },
  { role: 'Две школы', email: 'multi@fizmat.kz', password: 'MultiPassword123!', note: 'ученик в ФизМат и учитель в Школе №2 — переключатель' },
  { role: 'Админ Школы №2', email: 'admin@school2.kz', password: 'School2Password123!', note: 'другая организация — данные изолированы' },
]

export const showDemoAccounts = import.meta.env.VITE_SHOW_DEMO_ACCOUNTS !== 'false'
