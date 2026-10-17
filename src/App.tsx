/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Header } from './components/Header';
import { AcceptanceCriteriaView } from './components/AcceptanceCriteriaView';
import { ApiPlayground } from './components/ApiPlayground';
import { JwtTokenInspector } from './components/JwtTokenInspector';
import { CodeExplorer } from './components/CodeExplorer';
import { ClientCodeGenerator } from './components/ClientCodeGenerator';
import { ArchitectureGuide } from './components/ArchitectureGuide';
import { downloadProjectAsZip } from './utils/zipGenerator';
import { createJwtToken } from './utils/jwtHelper';
import { User, JwtTokens, Article } from './types';
import { Download, FileJson, Check, Terminal, ExternalLink, ShieldCheck, CheckCircle2 } from 'lucide-react';

const INITIAL_USER: User = {
  id: 1,
  email: 'admin@fizmat.kz',
  username: 'daniyar_admin',
  role: 'ADMIN',
  bio: 'Администратор образовательной платформы ФизМат Лицея',
  is_verified: true,
  created_at: new Date().toISOString(),
};

const INITIAL_ARTICLES: Article[] = [
  {
    id: 1,
    title: 'Алгебра 10 класс: Тригонометрические функции',
    slug: 'math-grade-10-trig',
    content:
      'Полный курс видеоуроков с доступом по ссылке YouTube, конспектами и проверочными тестами.',
    status: 'PUBLISHED',
    status_display: 'Опубликовано',
    author: {
      id: 1,
      email: 'teacher@fizmat.kz',
      username: 'aigul_teacher',
      role: 'ADMIN',
    },
    views_count: 248,
    tags: 'математика,тригонометрия,10класс',
    created_at: '2026-10-14T10:00:00Z',
    updated_at: '2026-10-14T10:00:00Z',
  },
  {
    id: 2,
    title: 'Подготовка к ЕНТ по Физике: Механика и Динамика',
    slug: 'ent-physics-mechanics',
    content:
      'Разбор типовых задач экзамена, формулы и тренировочные варианты в режиме Mock Exam.',
    status: 'PUBLISHED',
    status_display: 'Опубликовано',
    author: {
      id: 2,
      email: 'teacher@fizmat.kz',
      username: 'aigul_teacher',
      role: 'USER',
    },
    views_count: 184,
    tags: 'ент,физика,экзамены',
    created_at: '2026-10-15T14:30:00Z',
    updated_at: '2026-10-15T14:30:00Z',
  },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('criteria');
  const [currentRole, setCurrentRole] = useState<string>('student');
  const [currentLang, setCurrentLang] = useState<string>('ru');

  const [currentUser, setCurrentUser] = useState<User | null>(INITIAL_USER);
  const [isBlacklisted, setIsBlacklisted] = useState<boolean>(false);
  const [articles, setArticles] = useState<Article[]>(INITIAL_ARTICLES);
  const [isDownloading, setIsDownloading] = useState<boolean>(false);
  const [downloadSuccess, setDownloadSuccess] = useState<boolean>(false);

  // Initialize initial tokens for demo
  const [tokens, setTokens] = useState<JwtTokens | null>(() => {
    const acc = createJwtToken(INITIAL_USER, 'access', 15 * 60);
    const ref = createJwtToken(INITIAL_USER, 'refresh', 30 * 24 * 3600);
    return {
      access: acc.token,
      refresh: ref.token,
      accessExpiresAt: acc.expiresAtMs,
      refreshExpiresAt: ref.expiresAtMs,
    };
  });

  const handleDownloadZip = async () => {
    try {
      setIsDownloading(true);
      await downloadProjectAsZip();
      setDownloadSuccess(true);
      setTimeout(() => setDownloadSuccess(false), 3000);
    } catch (e) {
      console.error('Download error:', e);
    } finally {
      setIsDownloading(false);
    }
  };

  const handleFastForwardExpiry = () => {
    if (!tokens) return;
    setTokens({
      ...tokens,
      accessExpiresAt: Date.now() - 5000,
    });
  };

  const handleRefreshTokens = () => {
    if (!currentUser || isBlacklisted) return;
    const acc = createJwtToken(currentUser, 'access', 15 * 60);
    const ref = createJwtToken(currentUser, 'refresh', 30 * 24 * 3600);
    setTokens({
      access: acc.token,
      refresh: ref.token,
      accessExpiresAt: acc.expiresAtMs,
      refreshExpiresAt: ref.expiresAtMs,
    });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Header */}
      <Header
        onDownloadZip={handleDownloadZip}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentRole={currentRole}
        onChangeRole={setCurrentRole}
        currentLang={currentLang}
        onChangeLang={setCurrentLang}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Banner with Stats & Tech Stack */}
        <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-950/40 via-slate-900 to-slate-900 border border-indigo-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <span>EduPlatform Server REST API (Django 5, PostgreSQL 16, Celery, Redis)</span>
                <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1.5 py-0.5 rounded font-mono font-medium">
                  {currentLang.toUpperCase()} &bull; Роль: {currentRole}
                </span>
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                Защита YouTube unlisted &bull; Банк из 30 вопросов &bull; Автопроверка тестов &bull; Античит &bull; Multi-Tenant Org Isolation
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleDownloadZip}
              disabled={isDownloading}
              className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-indigo-900/30 transition flex items-center gap-1.5 cursor-pointer"
            >
              {downloadSuccess ? (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span>Архив готов!</span>
                </>
              ) : (
                <>
                  <Download className="w-3.5 h-3.5" />
                  <span>{isDownloading ? 'Архивация...' : 'Скачать бэкенд (.ZIP)'}</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Tab 1: 5 Acceptance Criteria Live Verifier */}
        {activeTab === 'criteria' && <AcceptanceCriteriaView />}

        {/* Tab 2: Interactive API Playground */}
        {activeTab === 'playground' && (
          <div className="space-y-6">
            <JwtTokenInspector
              tokens={tokens}
              onFastForwardExpiry={handleFastForwardExpiry}
              onRefreshTokens={handleRefreshTokens}
              isBlacklisted={isBlacklisted}
            />

            <ApiPlayground
              currentUser={currentUser}
              setCurrentUser={setCurrentUser}
              tokens={tokens}
              setTokens={setTokens}
              articles={articles}
              setArticles={setArticles}
              isBlacklisted={isBlacklisted}
              setIsBlacklisted={setIsBlacklisted}
            />
          </div>
        )}

        {/* Tab 3: Python / Django Source Code Explorer */}
        {activeTab === 'code' && <CodeExplorer />}

        {/* Tab 4: Client Code Generator */}
        {activeTab === 'client' && <ClientCodeGenerator tokens={tokens} />}

        {/* Tab 5: Architecture, RBAC & Documentation Guide */}
        {activeTab === 'guide' && <ArchitectureGuide />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 px-6 text-center text-xs text-slate-500">
        <p>
          EduPlatform REST API &bull; Python 3.12 &bull; Django 5 &bull; Django REST Framework &bull; PostgreSQL 16 &bull; Redis &bull; Celery
        </p>
      </footer>
    </div>
  );
}
