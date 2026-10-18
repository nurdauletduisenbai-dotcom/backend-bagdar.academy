import type { Role } from '@/types/api'

export const roleLabels: Record<Role, string> = {
  admin: 'Администратор',
  teacher: 'Учитель',
  curator: 'Куратор',
  student: 'Ученик',
  parent: 'Родитель',
}

export const courseTypeLabels: Record<string, string> = {
  school_subject: 'Школьный предмет',
  exam_prep: 'Подготовка к экзамену',
  club: 'Кружок',
}

export const courseStatusLabels: Record<string, string> = {
  draft: 'Черновик',
  published: 'Опубликован',
  archived: 'В архиве',
}

export const questionTypeLabels: Record<string, string> = {
  single: 'Один ответ',
  multi: 'Несколько ответов',
  short: 'Короткий текст',
  number: 'Число',
  match: 'Сопоставление',
  open: 'Развёрнутый ответ',
}

export const testModeLabels: Record<string, string> = {
  practice: 'Практика',
  quiz: 'Квиз',
  exam: 'Экзамен',
  mock_exam: 'Пробный экзамен',
}

export const attemptStatusLabels: Record<string, string> = {
  in_progress: 'В процессе',
  submitted: 'Ждёт проверки',
  expired: 'Время истекло',
  graded: 'Оценено',
}

export const submissionStatusLabels: Record<string, string> = {
  submitted: 'Ждёт проверки',
  graded: 'Проверено',
  returned: 'На доработке',
  pending: 'Не сдано',
  overdue: 'Просрочено',
}

export const attendanceLabels: Record<string, string> = {
  present: 'Был',
  absent: 'Не был',
  late: 'Опоздал',
  excused: 'Уважительная',
}

export const orderStatusLabels: Record<string, string> = {
  pending: 'Ожидает оплаты',
  paid: 'Оплачен',
  failed: 'Отменён',
  refunded: 'Возврат',
}

export const enrollmentStatusLabels: Record<string, string> = {
  active: 'Активна',
  expired: 'Истекла',
  canceled: 'Отменена',
  suspended: 'Приостановлена',
}

const dateFmt = new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
const dateTimeFmt = new Intl.DateTimeFormat('ru-RU', {
  day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
})
const timeFmt = new Intl.DateTimeFormat('ru-RU', { hour: '2-digit', minute: '2-digit' })

export const fmtDate = (v?: string | null) => (v ? dateFmt.format(new Date(v)) : '—')
export const fmtDateTime = (v?: string | null) => (v ? dateTimeFmt.format(new Date(v)) : '—')
export const fmtTime = (v?: string | null) => (v ? timeFmt.format(new Date(v)) : '—')

export function fmtMoney(value: string | number, currency = 'KZT') {
  const n = Number(value)
  if (!n) return 'Бесплатно'
  return `${n.toLocaleString('ru-RU')} ${currency === 'KZT' ? '₸' : currency}`
}

export function fmtDuration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

export function fmtBytes(bytes: number) {
  if (!bytes) return ''
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} КБ`
  return `${(bytes / 1024 / 1024).toFixed(1)} МБ`
}

/** ISO-строка -> значение для <input type="datetime-local"> */
export function toLocalInput(v?: string | null) {
  if (!v) return ''
  const d = new Date(v)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/** Значение <input type="datetime-local"> -> ISO-строка с часовым поясом */
export const fromLocalInput = (v: string) => (v ? new Date(v).toISOString() : null)
