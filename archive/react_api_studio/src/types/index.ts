export type UserRole = 'USER' | 'MODERATOR' | 'ADMIN';

export interface User {
  id: number;
  email: string;
  username: string;
  role: UserRole;
  bio?: string;
  is_verified: boolean;
  created_at: string;
}

export interface JwtTokens {
  access: string;
  refresh: string;
  accessExpiresAt: number; // timestamp ms
  refreshExpiresAt: number; // timestamp ms
}

export interface DecodedJwtPayload {
  token_type: 'access' | 'refresh';
  exp: number;
  iat: number;
  jti: string;
  user_id: number;
  email?: string;
  username?: string;
  role?: UserRole;
  is_verified?: boolean;
}

export interface Article {
  id: number;
  title: string;
  slug: string;
  content: string;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  status_display: string;
  author: {
    id: number;
    email: string;
    username: string;
    role: UserRole;
  };
  views_count: number;
  tags: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectFile {
  path: string;
  name: string;
  category: 'config' | 'accounts' | 'core_api' | 'docker' | 'tests' | 'docs';
  language: 'python' | 'json' | 'yaml' | 'markdown' | 'dockerfile' | 'env';
  content: string;
  description: string;
}

export interface RequestLog {
  id: string;
  timestamp: string;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  endpoint: string;
  status: number;
  durationMs: number;
  requestHeaders: Record<string, string>;
  requestBody?: any;
  responseHeaders: Record<string, string>;
  responseBody: any;
}
