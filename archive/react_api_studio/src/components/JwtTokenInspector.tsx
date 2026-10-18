import React, { useState, useEffect } from 'react';
import { KeyRound, Clock, ShieldAlert, CheckCircle2, RotateCcw, AlertTriangle, Copy, Check } from 'lucide-react';
import { decodeJwt } from '../utils/jwtHelper';
import { JwtTokens } from '../types';

interface JwtTokenInspectorProps {
  tokens: JwtTokens | null;
  onFastForwardExpiry: () => void;
  onRefreshTokens: () => void;
  isBlacklisted?: boolean;
}

export const JwtTokenInspector: React.FC<JwtTokenInspectorProps> = ({
  tokens,
  onFastForwardExpiry,
  onRefreshTokens,
  isBlacklisted,
}) => {
  const [selectedTokenType, setSelectedTokenType] = useState<'access' | 'refresh'>('access');
  const [copied, setCopied] = useState(false);
  const [remainingSeconds, setRemainingSeconds] = useState<number>(0);

  const activeRawToken = tokens ? (selectedTokenType === 'access' ? tokens.access : tokens.refresh) : '';
  const decoded = activeRawToken ? decodeJwt(activeRawToken) : null;

  useEffect(() => {
    if (!tokens) {
      setRemainingSeconds(0);
      return;
    }

    const targetExpiry = selectedTokenType === 'access' ? tokens.accessExpiresAt : tokens.refreshExpiresAt;
    const updateCountdown = () => {
      const diffSec = Math.max(0, Math.floor((targetExpiry - Date.now()) / 1000));
      setRemainingSeconds(diffSec);
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
    return () => clearInterval(interval);
  }, [tokens, selectedTokenType]);

  const copyToken = () => {
    if (!activeRawToken) return;
    navigator.clipboard.writeText(activeRawToken);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatCountdown = (sec: number) => {
    if (sec <= 0) return 'Истек (Expired)';
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    const h = Math.floor(m / 60);
    if (h > 0) return `${h}ч ${m % 60}м ${s}с`;
    return `${m}м ${s < 10 ? '0' : ''}${s}с`;
  };

  if (!tokens || !activeRawToken) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-center">
        <div className="inline-flex p-3 rounded-full bg-slate-800 text-slate-400 mb-3">
          <KeyRound className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-slate-200">JWT Токены не получены</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
          Выполните регистрацию (<code className="text-emerald-400 font-mono">/register/</code>) или вход (
          <code className="text-emerald-400 font-mono">/token/</code>) в песочнице, чтобы исследовать структуру полезной
          нагрузки (claims), подпись HS256 и жизненный цикл токенов.
        </p>
      </div>
    );
  }

  const parts = activeRawToken.split('.');

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      {/* Header with Switcher */}
      <div className="px-4 py-3 bg-slate-950/60 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <KeyRound className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-semibold text-slate-200 tracking-wide uppercase">
            Инспектор JWT Токена (SimpleJWT)
          </span>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex bg-slate-800 rounded-lg p-0.5 border border-slate-700/60 text-xs">
            <button
              onClick={() => setSelectedTokenType('access')}
              className={`px-3 py-1 rounded-md font-mono text-[11px] font-medium transition cursor-pointer ${
                selectedTokenType === 'access'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Access Token (15m)
            </button>
            <button
              onClick={() => setSelectedTokenType('refresh')}
              className={`px-3 py-1 rounded-md font-mono text-[11px] font-medium transition cursor-pointer ${
                selectedTokenType === 'refresh'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Refresh Token (7d)
            </button>
          </div>

          <button
            onClick={copyToken}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition cursor-pointer"
            title="Копировать токен"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Token Expiry & Status Alert */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg bg-slate-950/50 border border-slate-800">
          <div className="flex items-center gap-2.5">
            <Clock className={`w-4 h-4 ${remainingSeconds > 0 ? 'text-amber-400' : 'text-rose-400'}`} />
            <div>
              <div className="text-[11px] text-slate-400">Срок действия:</div>
              <div
                className={`text-xs font-mono font-bold ${
                  remainingSeconds > 0 ? 'text-slate-200' : 'text-rose-400'
                }`}
              >
                {formatCountdown(remainingSeconds)}
              </div>
            </div>
          </div>

          {isBlacklisted && selectedTokenType === 'refresh' ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs font-medium">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
              <span>Токен в Blacklist (Аннулирован)</span>
            </div>
          ) : remainingSeconds === 0 ? (
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1 text-xs text-rose-400 font-medium">
                <AlertTriangle className="w-3.5 h-3.5" /> Токен истек
              </span>
              <button
                onClick={onRefreshTokens}
                className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium flex items-center gap-1 transition cursor-pointer"
              >
                <RotateCcw className="w-3 h-3" /> Обновить токен
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" /> Активен
              </span>
              {selectedTokenType === 'access' && (
                <button
                  onClick={onFastForwardExpiry}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[11px] font-medium transition cursor-pointer"
                  title="Симулировать истечение срока действия токена для тестирования refresh-сценария"
                >
                  Истечь сейчас (+15 мин)
                </button>
              )}
            </div>
          )}
        </div>

        {/* Visual 3-Part JWT Representation (jwt.io style) */}
        <div>
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1.5">
            <span>Структура токена (Base64Url):</span>
            <div className="flex items-center gap-3 font-mono text-[10px]">
              <span className="text-rose-400">&bull; Header</span>
              <span className="text-purple-400">&bull; Payload</span>
              <span className="text-cyan-400">&bull; Signature</span>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs break-all leading-relaxed select-all">
            <span className="text-rose-400">{parts[0]}</span>
            <span className="text-slate-600">.</span>
            <span className="text-purple-400">{parts[1]}</span>
            <span className="text-slate-600">.</span>
            <span className="text-cyan-400">{parts[2]}</span>
          </div>
        </div>

        {/* Decoded Blocks Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {/* Header */}
          <div className="p-3 rounded-lg bg-slate-950/70 border border-rose-500/20">
            <div className="text-[11px] font-bold text-rose-400 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Заголовок (Header)</span>
              <span className="text-[10px] text-slate-500 font-mono">Algorithm: HS256</span>
            </div>
            <pre className="text-xs font-mono text-slate-300 overflow-x-auto">
              {JSON.stringify(decoded?.header, null, 2)}
            </pre>
          </div>

          {/* Payload (Claims) */}
          <div className="p-3 rounded-lg bg-slate-950/70 border border-purple-500/20">
            <div className="text-[11px] font-bold text-purple-400 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Полезная нагрузка (Payload Claims)</span>
              <span className="text-[10px] text-slate-500 font-mono">
                {selectedTokenType === 'access' ? 'Access Token' : 'Refresh Token'}
              </span>
            </div>
            <pre className="text-xs font-mono text-slate-300 overflow-x-auto">
              {JSON.stringify(decoded?.payload, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};
