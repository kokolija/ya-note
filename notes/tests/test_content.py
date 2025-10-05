from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.reader = User.objects.create(username='Кто-то другой')
        cls.note = Note.objects.create(text='Какой-то текст',
                                       author=cls.author)

    def test_notes_list_for_different_users(self):
        users_statuses = (
            (self.author, True),
            (self.reader, False),
        )
        for user, note_in_list in users_statuses:
            self.client.force_login(user)
            url = reverse('notes:list')
            response = self.client.get(url)
            object_list = response.context['object_list']
            assert (self.note in object_list) is note_in_list

    def test_pages_contains_form(self):
        self.client.force_login(self.author)
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for name, slug in urls:
            with self.subTest(name=name, slug=slug):
                url = reverse(name, args=slug)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
