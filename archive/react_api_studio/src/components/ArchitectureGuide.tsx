import React from 'react';
import { ShieldCheck, RefreshCw, Lock, Terminal, CheckCircle2, AlertTriangle, Key, Layers, Server } from 'lucide-react';

export const ArchitectureGuide: React.FC = () => {
  return (
    <div className="space-y-6 text-xs text-slate-300">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-3">
            <Key className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-slate-200 mb-1">Access Token (Короткий)</h3>
          <p className="text-slate-400 leading-relaxed">
            Время жизни <strong>15 минут</strong>. Содержит зашитые клеймы (<code className="text-emerald-400 font-mono">user_id</code>, <code className="text-emerald-400 font-mono">email</code>, <code className="text-emerald-400 font-mono">role</code>). Передается в заголовке <code className="text-emerald-400 font-mono">Authorization: Bearer</code> без постоянных запросов к БД.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-3">
            <RefreshCw className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-slate-200 mb-1">Refresh Token (Длинный)</h3>
          <p className="text-slate-400 leading-relaxed">
            Время жизни <strong>7 дней</strong>. Используется исключительно для запроса на <code className="text-indigo-400 font-mono">/token/refresh/</code>. При включенной ротации при каждом обновлении выдается свежий refresh токен, а старый сжигается.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="w-8 h-8 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center mb-3">
            <Lock className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-slate-200 mb-1">Token Blacklist (Черный список)</h3>
          <p className="text-slate-400 leading-relaxed">
            Реализует безопасный логаут. Модуль <code className="text-rose-400 font-mono">rest_framework_simplejwt.token_blacklist</code> записывает отозванный токен в таблицу базы данных, предотвращая повторный вход.
          </p>
        </div>
      </div>

      {/* Visual Sequence Flow */}
      <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
          <Layers className="w-4 h-4 text-emerald-400" />
          Жизненный цикл аутентификации JWT в Django REST Framework
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-center">
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <div className="text-emerald-400 font-bold mb-1">1. Логин пользователя</div>
            <div className="font-mono text-[11px] text-slate-400">POST /api/v1/auth/token/</div>
            <p className="mt-2 text-[11px] text-slate-400">
              Клиент передает email/пароль. Django проверяет хеш и возвращает пару (Access + Refresh).
            </p>
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <div className="text-sky-400 font-bold mb-1">2. Доступ к данным</div>
            <div className="font-mono text-[11px] text-slate-400">Authorization: Bearer &lt;tok&gt;</div>
            <p className="mt-2 text-[11px] text-slate-400">
              DRF <code className="text-sky-400 font-mono">JWTAuthentication</code> проверяет криптографическую подпись HS256 без чтения БД.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <div className="text-amber-400 font-bold mb-1">3. Истечение Access (15m)</div>
            <div className="font-mono text-[11px] text-slate-400">401 Token is expired</div>
            <p className="mt-2 text-[11px] text-slate-400">
              Axios перехватчик отлавливает 401 и отправляет refresh токен на <code className="font-mono text-amber-400">/token/refresh/</code>.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <div className="text-purple-400 font-bold mb-1">4. Выход (Logout)</div>
            <div className="font-mono text-[11px] text-slate-400">POST /api/v1/auth/logout/</div>
            <p className="mt-2 text-[11px] text-slate-400">
              Refresh токен вносится в таблицу черного списка в БД и больше не сможет выпустить токены.
            </p>
          </div>
        </div>
      </div>

      {/* Security Best Practices */}
      <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Рекомендации по безопасности для Production
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2 p-3 rounded-lg bg-slate-950/60 border border-slate-800">
            <div className="font-semibold text-emerald-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" /> Хранение токенов
            </div>
            <p className="text-slate-400 leading-relaxed">
              В веб-приложениях с высокими требованиями к безопасности Refresh токен рекомендуется сохранять в <strong>HttpOnly, Secure, SameSite=Strict Cookies</strong>. Это полностью защищает токен от кражи через XSS уязвимости. Access токен при этом можно безопасно держать в оперативной памяти JavaScript (React state).
            </p>
          </div>

          <div className="space-y-2 p-3 rounded-lg bg-slate-950/60 border border-slate-800">
            <div className="font-semibold text-amber-400 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" /> Секретный ключ (SECRET_KEY)
            </div>
            <p className="text-slate-400 leading-relaxed">
              Ключ <code className="font-mono text-amber-400">SECRET_KEY</code> или <code className="font-mono text-amber-400">JWT_SECRET_KEY</code> никогда не должен попадать в репозиторий Git. Генерируйте строку длиной не менее 64 случайных символов и передавайте через переменную окружения в <code className="font-mono text-slate-300">.env</code>.
            </p>
          </div>
        </div>
      </div>

      {/* CLI Cheat Sheet */}
      <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
        <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
          <Terminal className="w-4 h-4 text-emerald-400" />
          Шпаргалка консольных команд Django
        </h3>

        <div className="font-mono text-xs bg-slate-950 rounded-lg p-3 space-y-2 border border-slate-800">
          <div>
            <span className="text-slate-500"># Создание файла миграций после изменения models.py:</span>
            <div className="text-emerald-400 font-semibold">python manage.py makemigrations accounts core_api</div>
          </div>
          <div>
            <span className="text-slate-500"># Применение миграций к БД (создание таблиц пользователей, токенов и статей):</span>
            <div className="text-emerald-400 font-semibold">python manage.py migrate</div>
          </div>
          <div>
            <span className="text-slate-500"># Создание суперпользователя (администратора):</span>
            <div className="text-emerald-400 font-semibold">python manage.py createsuperuser</div>
          </div>
          <div>
            <span className="text-slate-500"># Запуск набора автотестов JWT аутентификации и API:</span>
            <div className="text-emerald-400 font-semibold">python manage.py test tests</div>
          </div>
          <div>
            <span className="text-slate-500"># Очистка просроченных токенов из базы черного списка (рекомендуется для cron):</span>
            <div className="text-emerald-400 font-semibold">python manage.py flushexpiredtokens</div>
          </div>
        </div>
      </div>
    </div>
  );
};
