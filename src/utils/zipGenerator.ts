import JSZip from 'jszip';
import { EDU_PROJECT_FILES } from '../data/djangoProjectFiles';

export async function downloadProjectAsZip(): Promise<void> {
  const zip = new JSZip();

  // Add project files into zip
  for (const file of EDU_PROJECT_FILES) {
    zip.file(file.path, file.content);
  }

  // Also include root config files
  zip.file('requirements.txt', `# Python 3.12 & Django 5 Core
Django>=5.0.0,<5.2.0
djangorestframework>=3.15.0
djangorestframework-simplejwt>=5.3.1
django-cors-headers>=4.3.1
django-filter>=24.1
django-environ>=0.11.2
argon2-cffi>=23.1.0
cryptography>=42.0.5
pyotp>=2.9.0
celery>=5.3.6
redis>=5.0.3
drf-spectacular>=0.27.1
gunicorn>=21.2.0
psycopg2-binary>=2.9.9
pytest-django>=4.8.0
ruff>=0.3.4
`);

  zip.file('.env.example', `DJANGO_SECRET_KEY=edu-secret-key-change-in-production
DJANGO_DEBUG=True
DATABASE_URL=postgres://postgres:postgres@db:5432/edu_platform_db
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
`);

  zip.file('Makefile', `.PHONY: up down migrate test lint seed
up:
\tdocker compose up -d --build
down:
\tdocker compose down
migrate:
\tpython manage.py migrate
test:
\tpytest -v
lint:
\truff check .
seed:
\tpython seed_data.py
`);

  const blob = await zip.generateAsync({
    type: 'blob',
    compression: 'DEFLATE',
    compressionOptions: { level: 9 },
  });

  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'edu_platform_backend.zip';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
