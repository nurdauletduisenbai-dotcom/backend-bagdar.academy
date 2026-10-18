import React, { useState } from 'react';
import { FileCode, Copy, Check, Download, Search, Folder, Terminal } from 'lucide-react';
import { DJANGO_PROJECT_FILES } from '../data/djangoProjectFiles';
import { ProjectFile } from '../types';

export const CodeExplorer: React.FC = () => {
  const [activeFile, setActiveFile] = useState<ProjectFile>(DJANGO_PROJECT_FILES[3]); // Default to settings.py
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [copied, setCopied] = useState<boolean>(false);

  const categories = [
    { id: 'all', label: 'Все файлы' },
    { id: 'config', label: 'Конфигурация & Settings' },
    { id: 'accounts', label: 'Аутентификация (accounts)' },
    { id: 'core_api', label: 'API & Модели (core_api)' },
    { id: 'docker', label: 'Docker & Compose' },
    { id: 'tests', label: 'Автотесты' },
  ];

  const filteredFiles = DJANGO_PROJECT_FILES.filter((file: ProjectFile) => {
    const matchesCategory = selectedCategory === 'all' || file.category === selectedCategory;
    const matchesSearch =
      file.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
      file.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const copyCode = () => {
    navigator.clipboard.writeText(activeFile.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadSingleFile = () => {
    const blob = new Blob([activeFile.content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = activeFile.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const lines = activeFile.content.split('\n');

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* File Tree / Sidebar */}
      <div className="lg:col-span-4 space-y-3">
        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Поиск по файлам..."
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
        </div>

        {/* Category Pills */}
        <div className="flex flex-wrap gap-1.5">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition cursor-pointer ${
                selectedCategory === cat.id
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Files List */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden divide-y divide-slate-800/60 max-h-[560px] overflow-y-auto">
          {filteredFiles.map((file: ProjectFile) => {
            const isSelected = activeFile.path === file.path;
            return (
              <button
                key={file.path}
                onClick={() => setActiveFile(file)}
                className={`w-full text-left p-2.5 transition flex items-start gap-2.5 cursor-pointer ${
                  isSelected ? 'bg-emerald-950/30 text-white' : 'hover:bg-slate-800/40 text-slate-300'
                }`}
              >
                <FileCode
                  className={`w-4 h-4 mt-0.5 shrink-0 ${
                    isSelected ? 'text-emerald-400' : 'text-slate-500'
                  }`}
                />
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-xs font-semibold truncate">{file.path}</span>
                    {isSelected && <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shrink-0" />}
                  </div>
                  <p className="text-[10px] text-slate-400 line-clamp-1 mt-0.5">{file.description}</p>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Code Viewer */}
      <div className="lg:col-span-8 space-y-3">
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          {/* Header */}
          <div className="px-4 py-3 bg-slate-950/80 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold text-emerald-400">{activeFile.path}</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                  {activeFile.language}
                </span>
                <span className="text-[10px] font-mono text-slate-500">{lines.length} строк</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">{activeFile.description}</p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={downloadSingleFile}
                className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs font-medium transition flex items-center gap-1.5 cursor-pointer"
                title="Скачать файл"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Скачать</span>
              </button>

              <button
                onClick={copyCode}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition flex items-center gap-1.5 cursor-pointer shadow-sm"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-white" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Скопировано!' : 'Копировать код'}</span>
              </button>
            </div>
          </div>

          {/* Code Body with Line Numbers */}
          <div className="p-4 bg-slate-950 font-mono text-xs overflow-x-auto max-h-[600px] overflow-y-auto">
            <div className="table w-full">
              {lines.map((line, idx) => (
                <div key={idx} className="table-row hover:bg-slate-900/60 transition">
                  <span className="table-cell select-none text-right pr-4 text-slate-600 text-[11px] w-10">
                    {idx + 1}
                  </span>
                  <span className="table-cell whitespace-pre text-slate-200">{line || ' '}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
