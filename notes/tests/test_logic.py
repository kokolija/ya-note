from http import HTTPStatus

from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add')
        cls.reader = User.objects.create(username='Какой-то пользователь')
        cls.form_data = {
            'title': 'Какое-то название',
            'text': 'Какой-то текст',
            'slug': 'any_slug'
        }

    def test_anonymous_user_cant_create_note(self):
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        self.client.force_login(self.reader)
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_not_unique_slug(self):
        self.client.force_login(self.reader)
        self.client.post(self.url, data=self.form_data)
        self.form_data['title'] = 'Другое название'
        response = self.client.post(self.url, data=self.form_data)
        form = response.context['form']
        self.assertFormError(
            form=form,
            field='slug',
            errors=self.form_data['slug'] + WARNING
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_empty_slug(self):
        self.client.force_login(self.reader)
        self.form_data.pop('slug')
        response = self.client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])[:100]
        self.assertEqual(new_note.slug, expected_slug)


class TestEditDeleteNotes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Кто-то другой')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            text='Какой-то текст',
            author=cls.author
        )
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {
            'title': 'Какое-то название',
            'text': 'Другой текст',
            'slug': 'any_slug'
        }

    def test_author_can_edit_note(self):
        response = self.auth_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.form_data['text'])

    def test_other_user_cant_edit_note(self):
        note_result = self.note
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, note_result.title)
        self.assertEqual(self.note.text, note_result.text)
        self.assertEqual(self.note.slug, note_result.slug)

    def test_author_can_delete_note(self):
        response = self.auth_client.delete(self.delete_url)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_other_user_cant_delete_note(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
