import React, { useState } from 'react';
import {
  Send,
  Lock,
  Globe,
  CheckCircle,
  AlertCircle,
  Copy,
  Check,
  RefreshCw,
  Clock,
  Sparkles,
  ShieldAlert,
  ChevronRight,
  Database
} from 'lucide-react';
import { User, JwtTokens, Article, RequestLog } from '../types';
import { createJwtToken, decodeJwt } from '../utils/jwtHelper';

interface ApiPlaygroundProps {
  currentUser: User | null;
  setCurrentUser: (user: User | null) => void;
  tokens: JwtTokens | null;
  setTokens: (tokens: JwtTokens | null) => void;
  articles: Article[];
  setArticles: React.Dispatch<React.SetStateAction<Article[]>>;
  isBlacklisted: boolean;
  setIsBlacklisted: (val: boolean) => void;
}

interface EndpointDef {
  id: string;
  name: string;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  path: string;
  category: 'auth' | 'articles';
  isProtected: boolean;
  permissionNote: string;
  description: string;
  defaultBody?: any;
}

const ENDPOINTS: EndpointDef[] = [
  {
    id: 'register',
    name: 'Регистрация пользователя',
    method: 'POST',
    path: '/api/v1/auth/register/',
    category: 'auth',
    isProtected: false,
    permissionNote: 'AllowAny (Публичный)',
    description: 'Создает нового пользователя и сразу возвращает access + refresh токены.',
    defaultBody: {
      email: 'alex.developer@example.com',
      username: 'alex_dev',
      password: 'SuperSecretPassword123!',
      password_confirm: 'SuperSecretPassword123!',
      bio: 'Python & Django REST Framework разработчик',
    },
  },
  {
    id: 'login',
    name: 'Получение JWT токенов (Логин)',
    method: 'POST',
    path: '/api/v1/auth/token/',
    category: 'auth',
    isProtected: false,
    permissionNote: 'AllowAny (Публичный)',
    description: 'Аутентификация по Email/Password. Возвращает Access и Refresh токены с кастомными claims.',
    defaultBody: {
      email: 'alex.developer@example.com',
      password: 'SuperSecretPassword123!',
    },
  },
  {
    id: 'refresh',
    name: 'Обновление токена (Refresh)',
    method: 'POST',
    path: '/api/v1/auth/token/refresh/',
    category: 'auth',
    isProtected: false,
    permissionNote: 'AllowAny (с валидным Refresh токеном)',
    description: 'Получение нового Access токена по действуюшему Refresh токену (ротация включена).',
    defaultBody: {
      refresh: '{{REFRESH_TOKEN}}',
    },
  },
  {
    id: 'verify',
    name: 'Проверка токена (Verify)',
    method: 'POST',
    path: '/api/v1/auth/token/verify/',
    category: 'auth',
    isProtected: false,
    permissionNote: 'AllowAny',
    description: 'Проверяет подпись и валидность токена без обращения к базе данных.',
    defaultBody: {
      token: '{{ACCESS_TOKEN}}',
    },
  },
  {
    id: 'profile_get',
    name: 'Профиль пользователя (GET)',
    method: 'GET',
    path: '/api/v1/auth/profile/',
    category: 'auth',
    isProtected: true,
    permissionNote: 'IsAuthenticated (Требуется Bearer токен)',
    description: 'Возвращает данные текущего авторизованного пользователя из payload токена и БД.',
  },
  {
    id: 'profile_patch',
    name: 'Обновление профиля (PATCH)',
    method: 'PATCH',
    path: '/api/v1/auth/profile/',
    category: 'auth',
    isProtected: true,
    permissionNote: 'IsAuthenticated (Требуется Bearer токен)',
    description: 'Частичное обновление профиля пользователя (имя, био).',
    defaultBody: {
      username: 'alex_senior',
      bio: 'Senior Backend Engineer: Django, DRF, PostgreSQL, Docker',
    },
  },
  {
    id: 'logout',
    name: 'Выход и Blacklist токена',
    method: 'POST',
    path: '/api/v1/auth/logout/',
    category: 'auth',
    isProtected: true,
    permissionNote: 'IsAuthenticated (Blacklist refresh токена)',
    description: 'Добавляет Refresh токен в черный список в БД. Повторный refresh вернет 401 Unauthorized.',
    defaultBody: {
      refresh: '{{REFRESH_TOKEN}}',
    },
  },
  {
    id: 'articles_list',
    name: 'Список статей (GET)',
    method: 'GET',
    path: '/api/v1/articles/',
    category: 'articles',
    isProtected: false,
    permissionNote: 'IsAuthenticatedOrReadOnly (Чтение публично)',
    description: 'Получение списка статей с пагинацией, фильтрацией и вложенными данными автора.',
  },
  {
    id: 'articles_create',
    name: 'Создать статью (POST)',
    method: 'POST',
    path: '/api/v1/articles/',
    category: 'articles',
    isProtected: true,
    permissionNote: 'IsAuthenticated (Автор привязывается из request.user)',
    description: 'Создание новой статьи. Автор автоматически берется из расшифрованного JWT токена.',
    defaultBody: {
      title: 'Глубокое погружение в JWT в Django REST Framework',
      content: 'Статья об алгоритмах HS256/RS256, ротации refresh токенов и безопасности в production.',
      status: 'PUBLISHED',
      tags: 'django,drf,jwt,security',
    },
  },
  {
    id: 'articles_patch',
    name: 'Редактировать статью (PATCH)',
    method: 'PATCH',
    path: '/api/v1/articles/1/',
    category: 'articles',
    isProtected: true,
    permissionNote: 'IsOwnerOrReadOnly (Только автор статьи!)',
    description: 'Проверяет права доступа объекта. Если токен принадлежит другому автору — вернет 403 Forbidden.',
    defaultBody: {
      title: 'Обновленное руководство по Django REST Framework & JWT',
      status: 'PUBLISHED',
    },
  },
];

export const ApiPlayground: React.FC<ApiPlaygroundProps> = ({
  currentUser,
  setCurrentUser,
  tokens,
  setTokens,
  articles,
  setArticles,
  isBlacklisted,
  setIsBlacklisted,
}) => {
  const [selectedEndpoint, setSelectedEndpoint] = useState<EndpointDef>(ENDPOINTS[1]); // Default to login
  const [requestBodyText, setRequestBodyText] = useState<string>(() =>
    selectedEndpoint.defaultBody ? JSON.stringify(selectedEndpoint.defaultBody, null, 2) : ''
  );
  const [sendAuthHeader, setSendAuthHeader] = useState<boolean>(true);
  const [lastResponse, setLastResponse] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [copiedResponse, setCopiedResponse] = useState<boolean>(false);
  const [requestHistory, setRequestHistory] = useState<RequestLog[]>([]);

  // Update body template when switching endpoints
  const handleSelectEndpoint = (ep: EndpointDef) => {
    setSelectedEndpoint(ep);
    if (ep.defaultBody) {
      let templated = JSON.stringify(ep.defaultBody, null, 2);
      if (tokens) {
        templated = templated
          .replace('{{ACCESS_TOKEN}}', tokens.access)
          .replace('{{REFRESH_TOKEN}}', tokens.refresh);
      }
      setRequestBodyText(templated);
    } else {
      setRequestBodyText('');
    }
  };

  const handleSendRequest = async () => {
    setIsLoading(true);

    const startTime = performance.now();
    await new Promise((res) => setTimeout(res, 120 + Math.random() * 80));

    let parsedBody: any = null;
    if (requestBodyText.trim()) {
      try {
        let text = requestBodyText;
        if (tokens) {
          text = text
            .replace('{{ACCESS_TOKEN}}', tokens.access)
            .replace('{{REFRESH_TOKEN}}', tokens.refresh);
        }
        parsedBody = JSON.parse(text);
      } catch (e) {
        setIsLoading(false);
        setLastResponse({
          status: 400,
          statusText: 'Bad Request',
          headers: { 'Content-Type': 'application/json' },
          data: { detail: 'JSON Parse Error: некорректный формат тела запроса' },
          backendExplanation: 'Django выбросил 400 Bad Request при парсинге тела запроса JSONParser.',
        });
        return;
      }
    }

    // Determine auth status
    const effectiveToken = sendAuthHeader && tokens ? tokens.access : null;
    let isTokenValid = false;
    let decodedAccess: any = null;

    if (effectiveToken) {
      const decoded = decodeJwt(effectiveToken);
      if (decoded.isValidFormat && !decoded.isExpired) {
        isTokenValid = true;
        decodedAccess = decoded.payload;
      }
    }

    let responseStatus = 200;
    let responseStatusText = 'OK';
    let responseData: any = {};
    let backendExplanation = '';

    // Simulate Django DRF Endpoint Logic
    switch (selectedEndpoint.id) {
      case 'register': {
        const { email, username, password, password_confirm, bio } = parsedBody || {};
        if (!email || !password) {
          responseStatus = 400;
          responseStatusText = 'Bad Request';
          responseData = {
            email: !email ? ['Это поле обязательно.'] : undefined,
            password: !password ? ['Это поле обязательно.'] : undefined,
          };
          backendExplanation = 'DRF RegisterSerializer: валидация обязательных полей не пройдена.';
        } else if (password !== password_confirm) {
          responseStatus = 400;
          responseStatusText = 'Bad Request';
          responseData = { password: ['Пароли не совпадают.'] };
          backendExplanation = 'RegisterSerializer.validate(): пароли не совпадают.';
        } else {
          const newUser: User = {
            id: Date.now() % 10000,
            email,
            username: username || email.split('@')[0],
            role: 'USER',
            bio: bio || '',
            is_verified: true,
            created_at: new Date().toISOString(),
          };
          setCurrentUser(newUser);

          const newAccess = createJwtToken(newUser, 'access', 15 * 60);
          const newRefresh = createJwtToken(newUser, 'refresh', 7 * 24 * 3600);
          const newTokens: JwtTokens = {
            access: newAccess.token,
            refresh: newRefresh.token,
            accessExpiresAt: newAccess.expiresAtMs,
            refreshExpiresAt: newRefresh.expiresAtMs,
          };
          setTokens(newTokens);
          setIsBlacklisted(false);

          responseStatus = 201;
          responseStatusText = 'Created';
          responseData = {
            message: 'Пользователь успешно зарегистрирован',
            user: {
              id: newUser.id,
              email: newUser.email,
              username: newUser.username,
              role: newUser.role,
              bio: newUser.bio,
              is_verified: newUser.is_verified,
            },
            tokens: {
              access: newTokens.access,
              refresh: newTokens.refresh,
            },
          };
          backendExplanation =
            'accounts.views.RegisterView: пользователь сохранен в БД (accounts_user), сгенерирована пара JWT токенов с кастомными claims.';
        }
        break;
      }

      case 'login': {
        const { email, password } = parsedBody || {};
        if (!email || !password) {
          responseStatus = 400;
          responseStatusText = 'Bad Request';
          responseData = { detail: 'Необходимо указать email и password' };
          backendExplanation = 'SimpleJWT TokenObtainPairSerializer: пустые учетные данные.';
        } else {
          // Success login
          const loggedUser: User = currentUser || {
            id: 101,
            email: email,
            username: email.split('@')[0],
            role: email.includes('admin') ? 'ADMIN' : 'USER',
            bio: 'Разработчик Django REST Framework',
            is_verified: true,
            created_at: new Date().toISOString(),
          };
          setCurrentUser(loggedUser);

          const newAccess = createJwtToken(loggedUser, 'access', 15 * 60);
          const newRefresh = createJwtToken(loggedUser, 'refresh', 7 * 24 * 3600);
          const newTokens: JwtTokens = {
            access: newAccess.token,
            refresh: newRefresh.token,
            accessExpiresAt: newAccess.expiresAtMs,
            refreshExpiresAt: newRefresh.expiresAtMs,
          };
          setTokens(newTokens);
          setIsBlacklisted(false);

          responseStatus = 200;
          responseStatusText = 'OK';
          responseData = {
            access: newTokens.access,
            refresh: newTokens.refresh,
            user: {
              id: loggedUser.id,
              email: loggedUser.email,
              username: loggedUser.username,
              role: loggedUser.role,
              is_verified: loggedUser.is_verified,
            },
          };
          backendExplanation =
            'CustomTokenObtainPairView: пароль проверен через Argon2/PBKDF2, возвращены JWT с полезной нагрузкой (claims: user_id, role, email).';
        }
        break;
      }

      case 'refresh': {
        const refreshInput = parsedBody?.refresh;
        if (!refreshInput) {
          responseStatus = 400;
          responseStatusText = 'Bad Request';
          responseData = { refresh: ['Это поле обязательно.'] };
          backendExplanation = 'TokenRefreshView: отсутствует параметр refresh в теле запроса.';
        } else if (isBlacklisted) {
          responseStatus = 401;
          responseStatusText = 'Unauthorized';
          responseData = {
            detail: 'Токен находится в черном списке (Token is blacklisted)',
            code: 'token_not_valid',
          };
          backendExplanation =
            'SimpleJWT token_blacklist: данный refresh токен был отозван при logout и больше не принимается сервером.';
        } else {
          const userForRefresh = currentUser || {
            id: 101,
            email: 'user@example.com',
            username: 'user',
            role: 'USER',
            is_verified: true,
            created_at: new Date().toISOString(),
          };
          const newAccess = createJwtToken(userForRefresh, 'access', 15 * 60);
          const newRefresh = createJwtToken(userForRefresh, 'refresh', 7 * 24 * 3600);

          setTokens({
            access: newAccess.token,
            refresh: newRefresh.token,
            accessExpiresAt: newAccess.expiresAtMs,
            refreshExpiresAt: newRefresh.expiresAtMs,
          });

          responseStatus = 200;
          responseStatusText = 'OK';
          responseData = {
            access: newAccess.token,
            refresh: newRefresh.token, // ROTATE_REFRESH_TOKENS = True
          };
          backendExplanation =
            'TokenRefreshView: Refresh токен валиден. Выдан новый access токен на 15 мин, а также новый refresh токен (ротация токенов SimpleJWT).';
        }
        break;
      }

      case 'verify': {
        const tokenToVerify = parsedBody?.token;
        if (!tokenToVerify) {
          responseStatus = 400;
          responseStatusText = 'Bad Request';
          responseData = { token: ['Это поле обязательно.'] };
          backendExplanation = 'TokenVerifyView: токен не передан.';
        } else {
          const check = decodeJwt(tokenToVerify);
          if (check.isValidFormat && !check.isExpired) {
            responseStatus = 200;
            responseStatusText = 'OK';
            responseData = {};
            backendExplanation = 'TokenVerifyView: токен криптографически валиден и срок действия не истек.';
          } else {
            responseStatus = 401;
            responseStatusText = 'Unauthorized';
            responseData = {
              detail: check.isExpired ? 'Срок действия токена истек.' : 'Токен поврежден или неверен.',
              code: 'token_not_valid',
            };
            backendExplanation = 'TokenVerifyView: токен отклонен аутентификацией DRF.';
          }
        }
        break;
      }

      case 'profile_get': {
        if (!isTokenValid) {
          responseStatus = 401;
          responseStatusText = 'Unauthorized';
          responseData = {
            detail: 'Учетные данные не были предоставлены или токен истек.',
            code: 'token_not_valid',
            messages: [
              {
                token_class: 'AccessToken',
                token_type: 'access',
                message: effectiveToken ? 'Срок действия токена истек.' : 'Заголовок Authorization: Bearer отсутствует.',
              },
            ],
          };
          backendExplanation =
            'accounts.views.UserProfileView: permission_classes = [IsAuthenticated] отклонил запрос без действующего JWT токена.';
        } else {
          const profileUser = currentUser || {
            id: decodedAccess.user_id,
            email: decodedAccess.email,
            username: decodedAccess.username,
            role: decodedAccess.role || 'USER',
            bio: 'Разработчик на Python',
            is_verified: decodedAccess.is_verified,
            created_at: new Date().toISOString(),
          };
          responseStatus = 200;
          responseStatusText = 'OK';
          responseData = {
            id: profileUser.id,
            email: profileUser.email,
            username: profileUser.username,
            role: profileUser.role,
            bio: profileUser.bio || '',
            is_verified: profileUser.is_verified,
            created_at: profileUser.created_at,
          };
          backendExplanation =
            'UserProfileView.get(): JWT успешно проверен `JWTAuthentication`, request.user аутентифицирован.';
        }
        break;
      }

      case 'profile_patch': {
        if (!isTokenValid) {
          responseStatus = 401;
          responseStatusText = 'Unauthorized';
          responseData = { detail: 'Учетные данные не были предоставлены.' };
          backendExplanation = 'UserProfileView: требует заголовок Authorization: Bearer <token>.';
        } else {
          const updated = {
            ...(currentUser || {
              id: decodedAccess.user_id,
              email: decodedAccess.email,
              role: 'USER',
              is_verified: true,
              created_at: new Date().toISOString(),
            }),
            username: parsedBody.username || currentUser?.username || 'user',
            bio: parsedBody.bio !== undefined ? parsedBody.bio : currentUser?.bio,
          };
          setCurrentUser(updated as User);

          responseStatus = 200;
          responseStatusText = 'OK';
          responseData = updated;
          backendExplanation = 'UserProfileView.partial_update(): профиль пользователя успешно обновлен в базе данных.';
        }
        break;
      }

      case 'logout': {
        if (!isTokenValid) {
          responseStatus = 401;
          responseStatusText = 'Unauthorized';
          responseData = { detail: 'Требуется авторизация для выхода.' };
          backendExplanation = 'LogoutView: permission_classes = [IsAuthenticated].';
        } else {
          setIsBlacklisted(true);
          responseStatus = 200;
          responseStatusText = 'OK';
          responseData = {
            detail: 'Успешный выход из системы. Refresh токен внесен в черный список (Blacklist).',
          };
          backendExplanation =
            'accounts.views.LogoutView: RefreshToken(token).blacklist() внес токен в таблицу `token_blacklist_outstandingtoken`.';
        }
        break;
      }

      case 'articles_list': {
        responseStatus = 200;
        responseStatusText = 'OK';
        responseData = {
          count: articles.length,
          next: null,
          previous: null,
          results: articles,
        };
        backendExplanation =
          'core_api.views.ArticleViewSet: публичный доступ через IsAuthenticatedOrReadOnly. Сработала стандартная PageNumberPagination.';
        break;
      }

      case 'articles_create': {
        if (!isTokenValid) {
          responseStatus = 401;
          responseStatusText = 'Unauthorized';
          responseData = {
            detail: 'Для публикации статьи требуется авторизация (Bearer JWT токен).',
          };
          backendExplanation =
            'ArticleViewSet.perform_create: IsAuthenticatedOrReadOnly заблокировал неавторизованную попытку записи (POST).';
        } else {
          const authorUser = currentUser || {
            id: decodedAccess.user_id,
            email: decodedAccess.email,
            username: decodedAccess.username || 'author',
            role: decodedAccess.role || 'USER',
          };

          const newArticle: Article = {
            id: articles.length + 1,
            title: parsedBody.title || 'Новая публикация',
            slug: (parsedBody.title || 'article')
              .toLowerCase()
              .replace(/[^a-z0-9]/g, '-')
              .substring(0, 30) + `-${Math.floor(Math.random() * 900 + 100)}`,
            content: parsedBody.content || 'Содержимое статьи...',
            status: parsedBody.status || 'PUBLISHED',
            status_display: parsedBody.status === 'DRAFT' ? 'Черновик' : 'Опубликовано',
            author: {
              id: authorUser.id,
              email: authorUser.email,
              username: authorUser.username,
              role: authorUser.role as any,
            },
            views_count: 0,
            tags: parsedBody.tags || 'drf,django',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };

          setArticles((prev) => [newArticle, ...prev]);

          responseStatus = 201;
          responseStatusText = 'Created';
          responseData = newArticle;
          backendExplanation =
            'ArticleViewSet.perform_create: статья создана, автор автоматически привязан из request.user (через JWT).';
        }
        break;
      }

      case 'articles_patch': {
        if (!isTokenValid) {
          responseStatus = 401;
          responseStatusText = 'Unauthorized';
          responseData = { detail: 'Учетные данные не были предоставлены.' };
          backendExplanation = 'ArticleViewSet: IsAuthenticatedOrReadOnly.';
        } else {
          // Check IsOwnerOrReadOnly
          const articleToEdit = articles[0];
          if (!articleToEdit) {
            responseStatus = 404;
            responseStatusText = 'Not Found';
            responseData = { detail: 'Страница не найдена.' };
            backendExplanation = 'ArticleViewSet: статья не найдена в БД.';
          } else {
            const isOwner =
              (currentUser && currentUser.id === articleToEdit.author.id) ||
              (decodedAccess && decodedAccess.user_id === articleToEdit.author.id) ||
              (decodedAccess && decodedAccess.role === 'ADMIN');

            if (!isOwner) {
              responseStatus = 403;
              responseStatusText = 'Forbidden';
              responseData = {
                detail: 'У вас нет разрешения на редактирование чужой статьи.',
              };
              backendExplanation =
                'accounts.permissions.IsOwnerOrReadOnly: отказ доступа 403! Пользователь не является автором статьи и не имеет прав администратора.';
            } else {
              const updatedArticle = {
                ...articleToEdit,
                title: parsedBody.title || articleToEdit.title,
                status: parsedBody.status || articleToEdit.status,
                updated_at: new Date().toISOString(),
              };
              setArticles((prev) => [updatedArticle, ...prev.slice(1)]);

              responseStatus = 200;
              responseStatusText = 'OK';
              responseData = updatedArticle;
              backendExplanation =
                'ArticleViewSet.partial_update: IsOwnerOrReadOnly подтвердил права автора, изменения успешно записаны.';
            }
          }
        }
        break;
      }
    }

    const duration = Math.round(performance.now() - startTime);

    const logEntry: RequestLog = {
      id: Math.random().toString(36).substring(2, 9),
      timestamp: new Date().toLocaleTimeString(),
      method: selectedEndpoint.method,
      endpoint: selectedEndpoint.path,
      status: responseStatus,
      durationMs: duration,
      requestHeaders: {
        'Content-Type': 'application/json',
        ...(effectiveToken ? { Authorization: `Bearer ${effectiveToken.substring(0, 16)}...` } : {}),
      },
      requestBody: parsedBody,
      responseHeaders: {
        'Content-Type': 'application/json',
        'X-Frame-Options': 'DENY',
        'Vary': 'Accept, Origin',
      },
      responseBody: responseData,
    };

    setRequestHistory((prev) => [logEntry, ...prev.slice(0, 14)]);
    setLastResponse({
      status: responseStatus,
      statusText: responseStatusText,
      headers: logEntry.responseHeaders,
      data: responseData,
      durationMs: duration,
      backendExplanation,
    });

    setIsLoading(false);
  };

  const copyResponseJson = () => {
    if (!lastResponse) return;
    navigator.clipboard.writeText(JSON.stringify(lastResponse.data, null, 2));
    setCopiedResponse(true);
    setTimeout(() => setCopiedResponse(false), 2000);
  };

  const getStatusBadgeColor = (status: number) => {
    if (status >= 200 && status < 300) return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    if (status === 401) return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    if (status === 403) return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
    return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
  };

  const getMethodColor = (m: string) => {
    switch (m) {
      case 'GET':
        return 'text-sky-400 bg-sky-950/60 border-sky-500/30';
      case 'POST':
        return 'text-emerald-400 bg-emerald-950/60 border-emerald-500/30';
      case 'PATCH':
      case 'PUT':
        return 'text-amber-400 bg-amber-950/60 border-amber-500/30';
      case 'DELETE':
        return 'text-rose-400 bg-rose-950/60 border-rose-500/30';
      default:
        return 'text-slate-400 bg-slate-800';
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Sidebar: Endpoints list */}
      <div className="lg:col-span-4 space-y-4">
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
          <div className="px-4 py-3 bg-slate-950/70 border-b border-slate-800 flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              Эндпоинты Django API
            </span>
            <span className="text-[10px] text-slate-400 font-mono">v1</span>
          </div>

          <div className="p-2 space-y-1 max-h-[600px] overflow-y-auto">
            {/* Category: Auth */}
            <div className="px-2 pt-2 pb-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Аутентификация и JWT (/api/v1/auth/)
            </div>
            {ENDPOINTS.filter((e) => e.category === 'auth').map((ep) => {
              const isSelected = selectedEndpoint.id === ep.id;
              return (
                <button
                  key={ep.id}
                  onClick={() => handleSelectEndpoint(ep)}
                  className={`w-full text-left p-2.5 rounded-lg border transition flex items-center justify-between gap-2 cursor-pointer ${
                    isSelected
                      ? 'bg-slate-800/90 border-emerald-500/50 shadow-sm'
                      : 'bg-slate-950/40 border-slate-800/60 hover:bg-slate-800/40 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${getMethodColor(
                        ep.method
                      )}`}
                    >
                      {ep.method}
                    </span>
                    <div className="truncate">
                      <div className="text-xs font-medium text-slate-200 truncate">{ep.name}</div>
                      <div className="text-[10px] text-slate-400 font-mono truncate">{ep.path}</div>
                    </div>
                  </div>
                  {ep.isProtected ? (
                    <span title="Требуется Bearer токен" className="shrink-0">
                      <Lock className="w-3.5 h-3.5 text-amber-400" />
                    </span>
                  ) : (
                    <span title="Публичный доступ" className="shrink-0">
                      <Globe className="w-3.5 h-3.5 text-slate-500" />
                    </span>
                  )}
                </button>
              );
            })}

            {/* Category: Articles */}
            <div className="px-2 pt-3 pb-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Бизнес-логика CRUD (/api/v1/articles/)
            </div>
            {ENDPOINTS.filter((e) => e.category === 'articles').map((ep) => {
              const isSelected = selectedEndpoint.id === ep.id;
              return (
                <button
                  key={ep.id}
                  onClick={() => handleSelectEndpoint(ep)}
                  className={`w-full text-left p-2.5 rounded-lg border transition flex items-center justify-between gap-2 cursor-pointer ${
                    isSelected
                      ? 'bg-slate-800/90 border-emerald-500/50 shadow-sm'
                      : 'bg-slate-950/40 border-slate-800/60 hover:bg-slate-800/40 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${getMethodColor(
                        ep.method
                      )}`}
                    >
                      {ep.method}
                    </span>
                    <div className="truncate">
                      <div className="text-xs font-medium text-slate-200 truncate">{ep.name}</div>
                      <div className="text-[10px] text-slate-400 font-mono truncate">{ep.path}</div>
                    </div>
                  </div>
                  {ep.isProtected ? (
                    <span title="Требуется Bearer токен" className="shrink-0">
                      <Lock className="w-3.5 h-3.5 text-amber-400" />
                    </span>
                  ) : (
                    <span title="Публичный доступ" className="shrink-0">
                      <Globe className="w-3.5 h-3.5 text-slate-500" />
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Column: Request & Response Workbench */}
      <div className="lg:col-span-8 space-y-4">
        {/* Request Panel */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
          {/* Endpoint Bar */}
          <div className="p-4 bg-slate-950/60 border-b border-slate-800">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
              <div className="flex items-center gap-2 min-w-0">
                <span
                  className={`text-xs font-mono font-bold px-2 py-1 rounded border ${getMethodColor(
                    selectedEndpoint.method
                  )}`}
                >
                  {selectedEndpoint.method}
                </span>
                <span className="text-sm font-mono font-semibold text-slate-200 truncate">
                  {selectedEndpoint.path}
                </span>
              </div>

              <button
                onClick={handleSendRequest}
                disabled={isLoading}
                className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium text-xs shadow-md shadow-emerald-900/30 transition flex items-center gap-2 cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Выполнение...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>Отправить запрос</span>
                  </>
                )}
              </button>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
              <p>{selectedEndpoint.description}</p>
              <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                {selectedEndpoint.permissionNote}
              </span>
            </div>
          </div>

          {/* Request Config (Headers + Body) */}
          <div className="p-4 space-y-3">
            {/* Headers Configuration */}
            <div className="p-3 rounded-lg bg-slate-950/50 border border-slate-800 text-xs space-y-2">
              <div className="font-semibold text-slate-300 flex items-center justify-between">
                <span>Заголовки запроса (HTTP Headers):</span>
                {selectedEndpoint.isProtected && (
                  <label className="flex items-center gap-2 font-normal text-slate-400 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={sendAuthHeader}
                      onChange={(e) => setSendAuthHeader(e.target.checked)}
                      className="rounded bg-slate-800 border-slate-700 text-emerald-500 focus:ring-0"
                    />
                    <span>Передавать заголовок Authorization</span>
                  </label>
                )}
              </div>

              <div className="space-y-1 font-mono text-[11px]">
                <div className="flex gap-2 text-slate-400">
                  <span className="text-slate-500 w-32 shrink-0">Content-Type:</span>
                  <span className="text-slate-300">application/json</span>
                </div>
                {selectedEndpoint.isProtected && (
                  <div className="flex gap-2">
                    <span className="text-slate-500 w-32 shrink-0">Authorization:</span>
                    {sendAuthHeader && tokens ? (
                      <span className="text-emerald-400 break-all">
                        Bearer {tokens.access.substring(0, 32)}...
                      </span>
                    ) : (
                      <span className="text-rose-400 italic">
                        {sendAuthHeader ? '[Токен отсутствует - вызовет 401]' : '[Заголовок отключен пользователем]'}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Request Body (if POST/PATCH/PUT) */}
            {['POST', 'PATCH', 'PUT'].includes(selectedEndpoint.method) && (
              <div>
                <div className="flex items-center justify-between text-xs text-slate-300 mb-1.5">
                  <span className="font-semibold">Тело запроса (JSON Body):</span>
                  <button
                    onClick={() => handleSelectEndpoint(selectedEndpoint)}
                    className="text-[11px] text-emerald-400 hover:underline flex items-center gap-1 cursor-pointer"
                  >
                    <RefreshCw className="w-3 h-3" /> Сбросить к шаблону
                  </button>
                </div>
                <textarea
                  value={requestBodyText}
                  onChange={(e) => setRequestBodyText(e.target.value)}
                  rows={6}
                  className="w-full font-mono text-xs bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-200 focus:outline-none focus:border-emerald-500 transition"
                  placeholder="{}"
                />
              </div>
            )}
          </div>
        </div>

        {/* Response Panel */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
          <div className="px-4 py-3 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                Ответ сервера (Response)
              </span>
              {lastResponse && (
                <span
                  className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${getStatusBadgeColor(
                    lastResponse.status
                  )}`}
                >
                  {lastResponse.status} {lastResponse.statusText}
                </span>
              )}
            </div>

            {lastResponse && (
              <div className="flex items-center gap-3 text-xs">
                <span className="text-slate-400 flex items-center gap-1 font-mono text-[11px]">
                  <Clock className="w-3 h-3" /> {lastResponse.durationMs}ms
                </span>
                <button
                  onClick={copyResponseJson}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition flex items-center gap-1 text-[11px] cursor-pointer"
                >
                  {copiedResponse ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedResponse ? 'Скопировано' : 'Копировать JSON'}</span>
                </button>
              </div>
            )}
          </div>

          <div className="p-4">
            {lastResponse ? (
              <div className="space-y-3">
                {/* DRF Behind-the-scenes explanation */}
                {lastResponse.backendExplanation && (
                  <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-xs">
                    <div className="flex items-center gap-1.5 font-semibold text-emerald-400 mb-1">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Что произошло в Django & DRF:</span>
                    </div>
                    <p className="text-slate-300">{lastResponse.backendExplanation}</p>
                  </div>
                )}

                {/* Formatted JSON */}
                <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-slate-200 overflow-x-auto max-h-[350px]">
                  {JSON.stringify(lastResponse.data, null, 2)}
                </pre>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500 text-xs">
                Нажмите <span className="text-emerald-400 font-medium">"Отправить запрос"</span>, чтобы получить ответ
                от имитируемого эндпоинта Django REST Framework.
              </div>
            )}
          </div>
        </div>

        {/* Recent Request History */}
        {requestHistory.length > 0 && (
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
              История недавних запросов:
            </div>
            <div className="space-y-1.5 max-h-36 overflow-y-auto">
              {requestHistory.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between text-xs font-mono p-1.5 rounded bg-slate-950/40 border border-slate-800/40"
                >
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${getMethodColor(item.method)}`}>
                      {item.method}
                    </span>
                    <span className="text-slate-300">{item.endpoint}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-[11px] font-bold ${getStatusBadgeColor(item.status)} px-1.5 rounded`}>
                      {item.status}
                    </span>
                    <span className="text-slate-500 text-[10px]">{item.durationMs}ms</span>
                    <span className="text-slate-500 text-[10px]">{item.timestamp}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
