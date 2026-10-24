from datetime import timedelta
from urllib.parse import quote

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.news.models import Post

URL = '/api/v1/news/posts/'

# 1×1 PNG
PNG = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
       b'\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82')


@pytest.mark.django_db
class TestPublicNews:
    def test_guest_sees_only_published(self, api):
        Post.objects.create(title='Опубликовано', body='Текст', is_published=True)
        Post.objects.create(title='Черновик', body='Текст', is_published=False)
        Post.objects.create(title='Отложено', body='Текст', is_published=True,
                            published_at=timezone.now() + timedelta(days=1))

        res = api.get(URL)
        assert res.status_code == 200
        assert [p['title'] for p in res.data['results']] == ['Опубликовано']
        assert 'body' not in res.data['results'][0]

    def test_detail_by_unicode_slug_and_draft_hidden(self, api):
        post = Post.objects.create(title='Жаңа оқу жылы', body='Бірінші абзац.\n\nЕкінші.', is_published=True)
        draft = Post.objects.create(title='Скрытая', body='x', is_published=False)
        assert post.slug == 'жаңа-оқу-жылы'

        res = api.get(f'{URL}{quote(post.slug)}/')
        assert res.status_code == 200
        assert res.data['body'].startswith('Бірінші')
        assert api.get(f'{URL}{quote(draft.slug)}/').status_code == 404

    def test_slug_is_unique_and_summary_falls_back_to_body(self):
        a = Post.objects.create(title='Итоги', body='слово ' * 100)
        b = Post.objects.create(title='Итоги', body='x', excerpt='Кратко')
        assert a.slug != b.slug
        assert a.summary.endswith('…') and len(a.summary) <= 220
        assert b.summary == 'Кратко'

    def test_pinned_first_and_ignores_invalid_token(self, api):
        Post.objects.create(title='Старая закреплённая', body='x', is_published=True, is_pinned=True,
                            published_at=timezone.now() - timedelta(days=10))
        Post.objects.create(title='Свежая', body='x', is_published=True)

        api.credentials(HTTP_AUTHORIZATION='Bearer broken')  # публичный эндпоинт не проверяет токен
        res = api.get(URL)
        assert res.status_code == 200
        assert [p['title'] for p in res.data['results']] == ['Старая закреплённая', 'Свежая']

    def test_cover_served_publicly(self, api, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path
        post = Post.objects.create(title='С обложкой', body='x', is_published=True,
                                   cover=SimpleUploadedFile('c.png', PNG, content_type='image/png'))
        item = api.get(URL).data['results'][0]
        assert item['cover_url']

        res = api.get(item['cover_url'])
        assert res.status_code == 200
        assert res['Content-Type'] == 'image/png'
        assert b''.join(res.streaming_content) == PNG
        assert api.get(f'{URL}{quote(Post.objects.create(title="Без", body="x", is_published=True).slug)}/cover/').status_code == 404
        assert post.cover.name.startswith('news/')

    def test_stats(self, api, make_user, org, course):
        make_user('s1@a.kz', 'student', org)
        make_user('t1@a.kz', 'teacher', org)
        res = api.get('/api/v1/news/stats/')
        assert res.status_code == 200
        assert res.data['students'] == 1 and res.data['teachers'] == 1 and res.data['schools'] >= 1
