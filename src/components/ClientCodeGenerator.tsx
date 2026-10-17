import React, { useState } from 'react';
import { Terminal, Copy, Check, Code2, Globe, Cpu } from 'lucide-react';
import { JwtTokens } from '../types';

interface ClientCodeGeneratorProps {
  tokens: JwtTokens | null;
}

export const ClientCodeGenerator: React.FC<ClientCodeGeneratorProps> = ({ tokens }) => {
  const [activeLang, setActiveLang] = useState<'curl' | 'python' | 'axios' | 'react'>('axios');
  const [copied, setCopied] = useState(false);

  const accessToken = tokens?.access || '<YOUR_ACCESS_TOKEN>';
  const refreshToken = tokens?.refresh || '<YOUR_REFRESH_TOKEN>';

  const codeSnippets = {
    curl: `# 1. Получение JWT токенов (Логин)
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \\
  -H "Content-Type: application/json" \\
  -d '{"email": "user@example.com", "password": "Password123!"}'

# 2. Выполнение защищенного запроса с заголовком Authorization: Bearer
curl -X GET http://127.0.0.1:8000/api/v1/auth/profile/ \\
  -H "Authorization: Bearer ${accessToken}"

# 3. Создание статьи (POST) авторизованным автором
curl -X POST http://127.0.0.1:8000/api/v1/articles/ \\
  -H "Authorization: Bearer ${accessToken}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Django REST Framework & JWT",
    "content": "Практический пример работы с токенами.",
    "status": "PUBLISHED",
    "tags": "django,jwt"
  }'

# 4. Обновление истекшего Access токена по Refresh токену
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/refresh/ \\
  -H "Content-Type: application/json" \\
  -d '{"refresh": "${refreshToken}"}'

# 5. Выход из системы (Blacklist токена)
curl -X POST http://127.0.0.1:8000/api/v1/auth/logout/ \\
  -H "Authorization: Bearer ${accessToken}" \\
  -H "Content-Type: application/json" \\
  -d '{"refresh": "${refreshToken}"}'`,

    python: `import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

class DjangoApiClient:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.login()

    def login(self):
        """Аутентификация и сохранение JWT пары"""
        res = requests.post(f"{BASE_URL}/auth/token/", json={
            "email": self.email,
            "password": self.password
        })
        res.raise_for_status()
        data = res.json()
        self.access_token = data["access"]
        self.refresh_token = data["refresh"]
        print(" Успешный вход! Токены получены.")

    def refresh(self):
        """Обновление access токена через refresh токен"""
        res = requests.post(f"{BASE_URL}/auth/token/refresh/", json={
            "refresh": self.refresh_token
        })
        if res.status_code == 200:
            data = res.json()
            self.access_token = data["access"]
            if "refresh" in data:
                self.refresh_token = data["refresh"]
            return True
        return False

    def request(self, method, endpoint, **kwargs):
        """Выполнение запроса с автоматическим перехватом 401 и refresh"""
        headers = kwargs.pop("headers", {})
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        url = f"{BASE_URL}{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)

        # Если access токен истек (401), пробуем обновиться и повторить запрос
        if response.status_code == 401 and self.refresh_token:
            print("Access токен истек, выполняем refresh...")
            if self.refresh():
                headers["Authorization"] = f"Bearer {self.access_token}"
                return requests.request(method, url, headers=headers, **kwargs)

        return response

# Пример использования
if __name__ == "__main__":
    client = DjangoApiClient("user@example.com", "Password123!")

    # Получение профиля
    profile = client.request("GET", "/auth/profile/").json()
    print("Профиль:", profile)

    # Создание статьи
    res = client.request("POST", "/articles/", json={
        "title": "Новость из Python клиента",
        "content": "Создано через кастомный клиент Django API",
        "status": "PUBLISHED"
    })
    print("Созданная статья:", res.json())`,

    axios: `import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 1. Request Interceptor: подстановка Bearer токена
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = \`Bearer \${token}\`;
  }
  return config;
});

// 2. Response Interceptor: бесшовный тихий refresh при 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');

      if (refreshToken) {
        try {
          const { data } = await axios.post('http://127.0.0.1:8000/api/v1/auth/token/refresh/', {
            refresh: refreshToken,
          });

          // Сохраняем новый access токен
          localStorage.setItem('access_token', data.access);
          if (data.refresh) {
            localStorage.setItem('refresh_token', data.refresh); // ротация
          }

          // Повторяем исходный запрос с новым токеном
          originalRequest.headers.Authorization = \`Bearer \${data.access}\`;
          return api(originalRequest);
        } catch (refreshErr) {
          // Refresh токен тоже истек или в черном списке -> разлогиниваем
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;`,

    react: `import { useState, useEffect, createContext, useContext } from 'react';
import api from './api';

interface AuthContextType {
  user: any;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType>(null!);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Проверка текущей сессии при загрузке
    const token = localStorage.getItem('access_token');
    if (token) {
      api.get('/auth/profile/')
        .then(res => setUser(res.data))
        .catch(() => logout())
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const { data } = await api.post('/auth/token/', { email, password });
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    setUser(data.user);
  };

  const logout = async () => {
    const refresh = localStorage.getItem('refresh_token');
    if (refresh) {
      try {
        await api.post('/auth/logout/', { refresh });
      } catch (e) {
        // Игнорируем ошибки при отзыве
      }
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  if (loading) return <div>Загрузка профиля...</div>;

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);`,
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(codeSnippets[activeLang]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-4">
      {/* Header & Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/90 border border-slate-800 p-3 rounded-xl">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
            Клиентский код интеграции с Django API
          </span>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex bg-slate-800 rounded-lg p-0.5 border border-slate-700/60 text-xs">
            <button
              onClick={() => setActiveLang('axios')}
              className={`px-3 py-1 rounded-md font-mono text-[11px] font-medium transition cursor-pointer ${
                activeLang === 'axios' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Axios (JS/TS)
            </button>
            <button
              onClick={() => setActiveLang('python')}
              className={`px-3 py-1 rounded-md font-mono text-[11px] font-medium transition cursor-pointer ${
                activeLang === 'python' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Python (requests)
            </button>
            <button
              onClick={() => setActiveLang('curl')}
              className={`px-3 py-1 rounded-md font-mono text-[11px] font-medium transition cursor-pointer ${
                activeLang === 'curl' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              cURL (Bash)
            </button>
            <button
              onClick={() => setActiveLang('react')}
              className={`px-3 py-1 rounded-md font-mono text-[11px] font-medium transition cursor-pointer ${
                activeLang === 'react' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              React Context (useAuth)
            </button>
          </div>

          <button
            onClick={handleCopy}
            className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Скопировано!' : 'Копировать'}</span>
          </button>
        </div>
      </div>

      {/* Code Display */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="p-4 bg-slate-950 font-mono text-xs overflow-x-auto max-h-[550px] overflow-y-auto text-slate-200 leading-relaxed whitespace-pre">
          {codeSnippets[activeLang]}
        </div>
      </div>
    </div>
  );
};
