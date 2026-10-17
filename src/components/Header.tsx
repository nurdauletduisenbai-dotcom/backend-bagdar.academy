import React from 'react';
import { Download, Terminal, ShieldCheck, FileCode2, BookOpen, Layers, CheckCircle2, Globe2 } from 'lucide-react';

interface HeaderProps {
  onDownloadZip: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  currentRole: string;
  onChangeRole: (role: string) => void;
  currentLang: string;
  onChangeLang: (lang: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  onDownloadZip,
  activeTab,
  setActiveTab,
  currentRole,
  onChangeRole,
  currentLang,
  onChangeLang,
}) => {
  const roles = [
    { id: 'student', label: 'Ученик (Student)' },
    { id: 'parent', label: 'Родитель (Parent)' },
    { id: 'teacher', label: 'Учитель (Teacher)' },
    { id: 'curator', label: 'Куратор (Curator)' },
    { id: 'admin', label: 'Администратор (Admin)' },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-900/95 backdrop-blur sticky top-0 z-40">
      {/* Top Banner */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-indigo-500 to-sky-700 flex items-center justify-center shadow-lg shadow-indigo-500/20 font-bold text-white text-base tracking-wider">
            Edu
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-100 tracking-tight">
                EduPlatform <span className="text-indigo-400">REST API</span>
              </h1>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
                Python 3.12 &bull; Django 5 &bull; Postgres 16
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Серверная часть для школы/лицея: YouTube unlisted, тесты с античитом, 2FA, ротация токенов, Celery
            </p>
          </div>
        </div>

        {/* Action Controls & Role Simulator */}
        <div className="flex items-center flex-wrap gap-2.5">
          {/* Language Switcher */}
          <div className="flex items-center bg-slate-800 rounded-lg p-0.5 border border-slate-700 text-xs">
            <Globe2 className="w-3.5 h-3.5 text-slate-400 ml-1.5 mr-1" />
            {(['ru', 'kk', 'en'] as const).map((lang) => (
              <button
                key={lang}
                onClick={() => onChangeLang(lang)}
                className={`px-2 py-0.5 rounded font-mono text-[11px] uppercase font-semibold transition cursor-pointer ${
                  currentLang === lang ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {lang}
              </button>
            ))}
          </div>

          {/* Role selector */}
          <div className="flex items-center gap-1.5 bg-slate-800/80 px-2.5 py-1 rounded-lg border border-slate-700 text-xs">
            <span className="text-slate-400 text-[11px]">Роль:</span>
            <select
              value={currentRole}
              onChange={(e) => onChangeRole(e.target.value)}
              className="bg-transparent text-indigo-300 font-semibold focus:outline-none cursor-pointer"
            >
              {roles.map((r) => (
                <option key={r.id} value={r.id} className="bg-slate-900 text-slate-200">
                  {r.label}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={onDownloadZip}
            className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-md shadow-indigo-900/30 transition flex items-center gap-1.5 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Скачать проект (.zip)</span>
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex overflow-x-auto border-t border-slate-800/80 gap-1 text-xs font-medium">
        <button
          onClick={() => setActiveTab('criteria')}
          className={`py-2.5 px-4 flex items-center gap-2 border-b-2 transition whitespace-nowrap cursor-pointer ${
            activeTab === 'criteria'
              ? 'border-indigo-500 text-indigo-400 font-semibold bg-indigo-500/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>Критерии приёмки и сценарии (5/5)</span>
        </button>

        <button
          onClick={() => setActiveTab('playground')}
          className={`py-2.5 px-4 flex items-center gap-2 border-b-2 transition whitespace-nowrap cursor-pointer ${
            activeTab === 'playground'
              ? 'border-indigo-500 text-indigo-400 font-semibold bg-indigo-500/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Интерактивная песочница API</span>
        </button>

        <button
          onClick={() => setActiveTab('code')}
          className={`py-2.5 px-4 flex items-center gap-2 border-b-2 transition whitespace-nowrap cursor-pointer ${
            activeTab === 'code'
              ? 'border-indigo-500 text-indigo-400 font-semibold bg-indigo-500/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileCode2 className="w-4 h-4" />
          <span>Исходный код (Python / Django)</span>
        </button>

        <button
          onClick={() => setActiveTab('client')}
          className={`py-2.5 px-4 flex items-center gap-2 border-b-2 transition whitespace-nowrap cursor-pointer ${
            activeTab === 'client'
              ? 'border-indigo-500 text-indigo-400 font-semibold bg-indigo-500/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Terminal className="w-4 h-4" />
          <span>Клиентский код (cURL, Axios, React)</span>
        </button>

        <button
          onClick={() => setActiveTab('guide')}
          className={`py-2.5 px-4 flex items-center gap-2 border-b-2 transition whitespace-nowrap cursor-pointer ${
            activeTab === 'guide'
              ? 'border-indigo-500 text-indigo-400 font-semibold bg-indigo-500/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Архитектура, RBAC и Документация</span>
        </button>
      </div>
    </header>
  );
};
