from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.reader = User.objects.create(username='Кто-то другой')
        cls.note = Note.objects.create(text='Какой-то текст',
                                       author=cls.author)

    def test_page_availability_for_anonymous_user(self):
        urls = (
            ('notes:home', 'GET'),
            ('users:login', 'GET'),
            ('users:logout', 'POST'),
            ('users:signup', 'GET'))
        for name, method in urls:
            with self.subTest():
                url = reverse(name)
                if method == 'GET':
                    response = self.client.get(url)
                else:
                    response = self.client.post(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_availability_for_auth_user(self):
        urls = (
            'notes:list',
            'notes:success',
            'notes:add',
        )
        self.client.force_login(self.reader)
        for name in urls:
            with self.subTest():
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_availability_for_detail_edit_delete(self):
        urls = (
            'notes:detail',
            'notes:edit',
            'notes:delete'
        )
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_user(self):
        login_url = reverse('users:login')
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
            ('notes:detail', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:list', None),
            ('notes:success', None)
        )
        login_url = reverse('users:login')
        for name, slug in urls:
            with self.subTest(name=name, slug=slug):
                url = reverse(name, args=slug)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
