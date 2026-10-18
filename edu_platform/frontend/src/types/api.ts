// Типы ответов Django API. Источник правды — Swagger: http://localhost:8000/docs/

export type Role = 'admin' | 'teacher' | 'curator' | 'student' | 'parent'
export type ID = number

// ---------- Общее ----------

export interface Paginated<T> {
  total: number
  total_pages: number
  page: number
  page_size: number
  results: T[]
}

export interface ApiError {
  error: { code: string; message: string; details: Record<string, unknown> }
}

export interface Message {
  message: string
}

// ---------- Аккаунт ----------

export interface OrganizationBrief {
  id: ID
  name: string
  slug: string
  roles: Role[]
}

export interface AuthUser {
  id: ID
  email: string
  full_name: string
  is_verified: boolean
  org_id: ID | null
  roles: Role[]
  organizations: OrganizationBrief[]
}

export interface LoginSuccess {
  requires_2fa: false
  access_token: string
  refresh_token: string
  user: AuthUser
}

// 2FA включена: токены не выдаются, повторите вход с totp_code
export interface Login2faRequired {
  requires_2fa: true
}

export type LoginResponse = LoginSuccess | Login2faRequired

export interface RefreshResponse {
  access_token: string
  refresh_token: string
}

export interface UserProfile {
  id: ID
  email: string
  first_name: string
  last_name: string
  phone: string | null
  language: 'ru' | 'kk' | 'en'
  birth_date: string | null
  avatar_url: string | null
  is_verified: boolean
  is_minor: boolean
  roles: Role[]
  created_at: string
}

export interface AuthSession {
  id: ID
  device_info: string
  ip: string | null
  created_at: string
  expires_at: string
  is_current: boolean
}

export interface TwoFactorSetup {
  secret: string
  otpauth_uri: string
}

export interface PersonBrief {
  id: ID
  email: string
  full_name: string
}

export interface ParentRelation {
  id: ID
  parent: PersonBrief
  student: PersonBrief
  is_confirmed: boolean
  created_at: string
}

// ---------- Организация ----------

export interface Organization {
  id: ID
  name: string
  slug: string
  logo_url: string | null
  timezone: string
  is_active: boolean
  created_at: string
}

export interface Member {
  id: ID
  user: ID
  email: string
  full_name: string
  role: Role
  is_active: boolean
  created_at: string
}

export interface Invite {
  id: ID
  role: Role
  course: ID | null
  group: ID | null
  max_uses: number
  used_count: number
  expires_at: string
  is_valid?: boolean
  invite_token?: string
  created_at?: string
}

// ---------- Курсы ----------

export type CourseType = 'school_subject' | 'exam_prep' | 'club'
export type CourseStatus = 'draft' | 'published' | 'archived'

export interface Course {
  id: ID
  title: string
  slug: string
  description?: string
  type: CourseType
  subject: string
  grade_level: number | null
  price: string
  access_days: number
  status: CourseStatus
  is_free_preview_enabled: boolean
  created_at: string
}

export interface CourseLessonBrief {
  id: ID
  title: string
  order: number
  is_free_preview: boolean
  is_published: boolean
  videos: { id: ID; title: string; duration_seconds: number }[]
}

export interface CourseSectionBrief {
  id: ID
  title: string
  order: number
  lessons: CourseLessonBrief[]
}

export interface CourseTestBrief {
  id: ID
  title: string
  mode: string
  time_limit_minutes: number
  max_attempts: number
  lesson_id: ID | null
}

export interface CourseDetail extends Course {
  description: string
  sections: CourseSectionBrief[]
  tests: CourseTestBrief[]
  is_enrolled: boolean
}

export interface Enrollment {
  id: ID
  course: ID
  group: ID | null
  student: ID
  student_email: string
  status: 'active' | 'expired' | 'canceled' | 'suspended'
  access_until: string
  enrolled_at: string
}

export interface Group {
  id: ID
  course: ID
  name: string
  max_students: number
  is_active: boolean
  students_count: number
  created_at: string
}

// ---------- Контент ----------

export interface Section {
  id: ID
  course: ID
  title: string
  order: number
  lessons_count: number
  created_at: string
}

export interface Lesson {
  id: ID
  section: ID
  course_id: ID
  title: string
  order: number
  is_free_preview: boolean
  publish_at: string | null
  is_published: boolean
  created_at: string
}

export interface Material {
  id: ID
  lesson: ID
  title: string
  file_url: string
  file_type: string
  file_size_bytes: number
  order: number
  has_file: boolean
  download_url: string | null
  created_at: string
}

export interface LessonDetail extends Lesson {
  has_access: boolean
  is_completed: boolean
  videos: { id: ID; title: string; duration_seconds: number; order: number; is_completed: boolean }[]
  materials: Material[]
  assignments: { id: ID; title: string; deadline: string }[]
  tests: { id: ID; title: string; mode: string }[]
}

export interface Comment {
  id: ID
  lesson: ID
  parent: ID | null
  author: { id: ID; name: string }
  content: string
  is_hidden: boolean
  replies_count: number
  created_at: string
  updated_at: string
}

export interface VideoManage {
  id: ID
  lesson: ID
  title: string
  youtube_video_id: string | null
  duration_seconds: number
  order: number
  created_at: string
}

export interface VideoPlayer {
  video_id: ID
  title: string
  duration_seconds: number
  embed_url: string
  watched_seconds: number
  is_completed: boolean
}

// ---------- Вопросы и тесты ----------

export type QuestionType = 'single' | 'multi' | 'short' | 'number' | 'match' | 'open'

export interface Topic {
  id: ID
  subject: string
  name: string
  parent: ID | null
  questions_count: number
  created_at: string
}

export interface QuestionOption {
  id?: ID
  text: string
  is_correct: boolean
  match_target: string
  order?: number
}

export interface Question {
  id: ID
  topic: ID
  type: QuestionType
  text: string
  explanation: string
  difficulty: number
  tolerance: number
  version: number
  is_archived: boolean
  options: QuestionOption[]
  used_in_tests: number
  created_at: string
}

export type TestMode = 'practice' | 'quiz' | 'exam' | 'mock_exam'

export interface TestInfo {
  id: ID
  course: ID
  lesson: ID | null
  title: string
  description: string
  mode: TestMode
  time_limit_minutes: number
  max_attempts: number
  passing_score_pct: number
  shuffle_questions: boolean
  shuffle_options: boolean
  show_answers_after_submit: boolean
  available_from: string | null
  available_to: string | null
  questions_count: number
  attempts_used: number
  created_at: string
}

export interface TestQuestionManage {
  id: ID
  question: Question
  points: number
  order: number
}

export interface AttemptQuestion {
  id: ID
  type: QuestionType
  text: string
  points: number
  order: number
  options: { id: ID; text: string }[]
  match_targets?: string[]
  saved_answer: { selected_options: number[] | Record<string, string>; text_answer: string } | null
}

export type AttemptStatus = 'in_progress' | 'submitted' | 'expired' | 'graded'

export interface AttemptStarted {
  attempt_id: ID
  test_id: ID
  title: string
  time_limit_minutes: number
  started_at: string
  deadline: string | null
  max_score: number
  status: AttemptStatus
  questions: AttemptQuestion[]
}

export interface ReviewItem {
  question_id: ID
  type: QuestionType
  text: string
  points: number
  explanation: string
  options: { id: ID; text: string }[]
  correct_options: { id: ID; text: string; match_target: string | null }[]
  selected_options: number[] | Record<string, string>
  text_answer: string
  score: number
  is_correct: boolean
  teacher_feedback: string
}

export interface AttemptResult {
  attempt_id: ID
  test_id: ID
  status: AttemptStatus
  score: number
  max_score: number
  score_pct: number
  is_passed: boolean
  started_at: string
  submitted_at: string | null
  time_spent_seconds: number
  review: ReviewItem[] | null
}

export interface AttemptListItem {
  id: ID
  student: ID
  student_email: string
  status: AttemptStatus
  score: number
  max_score: number
  score_pct: number
  is_passed: boolean
  started_at: string
  submitted_at: string | null
}

export interface TestStats {
  test_id: ID
  attempts: number
  students: number
  average_score_pct: number
  pass_rate_pct: number
  anti_cheat_events: number
  questions: { question_id: ID; text: string; type: QuestionType; answered: number; correct_pct: number | null }[]
}

// ---------- Задания ----------

export type SubmissionStatus = 'submitted' | 'graded' | 'returned'

export interface Submission {
  id: ID
  assignment: ID
  assignment_title: string
  student: ID
  student_name: string
  student_email: string
  text_content: string
  file_url: string | null
  has_file: boolean
  download_url: string | null
  status: SubmissionStatus
  submitted_at: string
  is_late: boolean
  score: number | null
  feedback: string
  graded_at: string | null
  can_resubmit: boolean
}

export interface Assignment {
  id: ID
  lesson: ID
  course_id: ID
  title: string
  description: string
  deadline: string
  max_score: number
  accept_late: boolean
  is_overdue: boolean
  my_submission: Submission | null
  submissions_count: number | null
  created_at: string
}

// ---------- Расписание ----------

export interface ClassSession {
  id: ID
  group: ID
  group_name: string
  course_id: ID
  title: string
  start_time: string
  end_time: string
  location: string
  online_meeting_url: string | null
  lesson: ID | null
  is_canceled: boolean
  created_at: string
}

export type AttendanceStatus = 'present' | 'absent' | 'late' | 'excused'

export interface Attendance {
  id: ID
  session: ID
  session_title: string
  session_start: string
  student: ID
  student_name: string
  status: AttendanceStatus
  notes: string
}

export interface GroupStudent {
  student_id: ID
  email: string
  full_name: string
  access_until: string
}

// ---------- Уведомления ----------

export interface AppNotification {
  id: ID
  type: string
  title: string
  message: string
  is_read: boolean
  metadata: Record<string, unknown>
  created_at: string
}

export interface Announcement {
  id: ID
  org: ID
  course: ID | null
  title: string
  content: string
  author: string
  created_at: string
}

// ---------- Платежи ----------

export type OrderStatus = 'pending' | 'paid' | 'failed' | 'refunded'

export interface Order {
  id: ID
  course: ID
  course_title: string
  user: ID
  user_email: string
  amount: string
  currency: string
  status: OrderStatus
  provider: 'manual' | 'stripe' | 'kaspi'
  checkout_url: string
  paid_at: string | null
  refunded_at: string | null
  failure_reason: string
  created_at: string
}

// ---------- Прогресс ----------

export interface CourseProgressSummary {
  course_id: ID
  course_title: string
  enrollment_status: string
  access_until: string
  percent_completed: number
  average_test_score: number
}

export interface CourseReport {
  course_id: ID
  course_title: string
  percent_completed: number
  lessons_completed_count: number
  total_lessons_count: number
  average_test_score: number
  lessons: { id: ID; title: string; section: string; is_completed: boolean }[]
  tests: { id: ID; title: string; best_score_pct: number | null; attempts: number; passed: boolean }[]
  assignments: { id: ID; title: string; deadline: string; max_score: number; status: string; score: number | null }[]
  attendance: Record<string, number>
}

export interface CourseStudentRow {
  student_id: ID
  student_email: string
  student_name: string
  group: string | null
  enrollment_status: string
  percent_completed: number
  average_test_score: number
}

export interface OrgSummary {
  members_by_role: Record<string, number>
  courses_by_status: Record<string, number>
  active_enrollments: number
  average_progress_pct: number
  revenue_total: number | string
  revenue_30d: number | string
  orders_pending: number
}

export interface AuditLog {
  id: ID
  created_at: string
  action: string
  user: ID | null
  user_email: string | null
  ip_address: string | null
  request_id: string
  entity_type: string
  entity_id: ID | null
  changes: Record<string, unknown>
}
