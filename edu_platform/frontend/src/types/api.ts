// Типы ответов Django API (apps/*/serializers.py, apps/accounts/services.py)

export type Role = 'admin' | 'teacher' | 'curator' | 'student' | 'parent'

export interface AuthUser {
  id: number
  email: string
  full_name: string
  is_verified: boolean
  roles: Role[]
}

export interface LoginSuccess {
  requires_2fa: false
  access_token: string
  refresh_token: string
  user: AuthUser
}

export interface Login2faRequired {
  requires_2fa: true
  temp_token: string
}

export type LoginResponse = LoginSuccess | Login2faRequired

export interface RefreshResponse {
  access_token: string
  refresh_token: string
}

export interface UserProfile {
  id: number
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

// apps/common/pagination.py → StandardPagination
export interface Paginated<T> {
  total: number
  total_pages: number
  page: number
  page_size: number
  results: T[]
}

export type CourseType = 'school_subject' | 'exam_prep' | 'club'

export interface Course {
  id: number
  title: string
  slug: string
  type: CourseType
  subject: string
  grade_level: number | null
  price: string
  status: 'draft' | 'published' | 'archived'
  is_free_preview_enabled: boolean
  created_at: string
}

// apps/common/exceptions.py → custom_exception_handler
export interface ApiError {
  error: {
    code: string
    message: string
    details: Record<string, unknown>
  }
}
