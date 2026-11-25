import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Meme, MemeVote

User = get_user_model()


def make_image_file(name='meme.png'):
    """Генерирует маленькую PNG-картинку в памяти для тестов."""
    buf = io.BytesIO()
    Image.new('RGB', (40, 40), color=(232, 89, 12)).save(buf, format='PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


class TempMediaMixin:
    """На время каждого теста направляет MEDIA_ROOT во временную папку."""

    def setUp(self):
        super().setUp()
        self._temp_media = tempfile.mkdtemp()
        self._media_override = override_settings(MEDIA_ROOT=self._temp_media)
        self._media_override.enable()

    def tearDown(self):
        self._media_override.disable()
        shutil.rmtree(self._temp_media, ignore_errors=True)
        super().tearDown()


class MemeModelTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='student1')

    def test_published_filters_out_unapproved_memes(self):
        visible = Meme.objects.create(
            author=self.user,
            image=make_image_file('1.png'),
            caption='Опубликованный мем',
            is_published=True,
        )
        Meme.objects.create(
            author=self.user,
            image=make_image_file('2.png'),
            caption='На модерации',
            is_published=False,
        )
        self.assertEqual(list(Meme.objects.published()), [visible])

    def test_unique_vote_per_user_constraint(self):
        meme = Meme.objects.create(
            author=self.user,
            image=make_image_file(),
            is_published=True,
        )
        MemeVote.objects.create(meme=meme, user=self.user, value=1)
        with self.assertRaises(IntegrityError):
            MemeVote.objects.create(meme=meme, user=self.user, value=-1)


class MemeListAndSortTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user1 = User.objects.create_user(username='user1')
        self.user2 = User.objects.create_user(username='user2')

    def test_empty_feed_shows_placeholder(self):
        response = self.client.get(reverse('memes:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Опубликованных мемов пока нет.')

    def test_feed_shows_only_published_memes(self):
        Meme.objects.create(
            author=self.user1,
            image=make_image_file('pub.png'),
            caption='Когда сдал зачёт с первого раза',
            is_published=True,
        )
        Meme.objects.create(
            author=self.user1,
            image=make_image_file('mod.png'),
            caption='Скрытый мем на проверке',
            is_published=False,
        )
        response = self.client.get(reverse('memes:list'))
        self.assertContains(response, 'Когда сдал зачёт с первого раза')
        self.assertNotContains(response, 'Скрытый мем на проверке')

    def test_sort_new_and_top(self):
        older = Meme.objects.create(
            author=self.user1,
            image=make_image_file('old.png'),
            caption='Старый, но топовый мем',
            is_published=True,
        )
        newer = Meme.objects.create(
            author=self.user1,
            image=make_image_file('new.png'),
            caption='Свежий мем без голосов',
            is_published=True,
        )
        MemeVote.objects.create(meme=older, user=self.user1, value=1)
        MemeVote.objects.create(meme=older, user=self.user2, value=1)

        new_response = self.client.get(reverse('memes:list'))
        self.assertEqual(
            [m.pk for m in new_response.context['memes']],
            [newer.pk, older.pk],
        )

        top_response = self.client.get(reverse('memes:list') + '?sort=top')
        self.assertEqual(
            [m.pk for m in top_response.context['memes']],
            [older.pk, newer.pk],
        )


class MemeUploadTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='author')

    def test_anonymous_user_cannot_upload_meme(self):
        response = self.client.post(
            reverse('memes:list'),
            {'image': make_image_file(), 'caption': 'Мем от гостя'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response['Location'])
        self.assertFalse(Meme.objects.exists())

    def test_authenticated_user_upload_goes_to_moderation(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('memes:list'),
            {'image': make_image_file(), 'caption': '  Восьмая пара в пятницу  '},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        meme = Meme.objects.get()
        self.assertEqual(meme.author, self.user)
        self.assertEqual(meme.caption, 'Восьмая пара в пятницу')
        self.assertFalse(meme.is_published)
        self.assertContains(
            response,
            'Мем отправлен на модерацию и появится после проверки',
        )
        # Пока модератор не одобрил, в самой ленте мем не виден
        self.assertNotContains(response, 'Восьмая пара в пятницу')

    def test_upload_without_image_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('memes:list'),
            {'caption': 'Мем без файла'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Выберите картинку.')
        self.assertFalse(Meme.objects.exists())


class MemeVoteTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='voter')
        self.meme = Meme.objects.create(
            author=self.user,
            image=make_image_file(),
            caption='Мем для голосования',
            is_published=True,
        )
        self.vote_url = reverse('memes:vote', args=[self.meme.pk])

    def test_anonymous_user_cannot_vote(self):
        response = self.client.post(self.vote_url, {'value': '1'})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response['Location'])
        self.assertFalse(MemeVote.objects.exists())

    def test_upvote_toggle_and_switch_to_downvote(self):
        self.client.force_login(self.user)

        # 1) Ставим апвоут (+1)
        res1 = self.client.post(
            self.vote_url,
            {'value': '1'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json(), {'score': 1, 'user_vote': 1})

        # 2) Повторный клик на апвоут снимает голос (0)
        res2 = self.client.post(
            self.vote_url,
            {'value': '1'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(res2.json(), {'score': 0, 'user_vote': 0})

        # 3) Ставим апвоут, а затем переключаем на даунвоут (-1)
        self.client.post(self.vote_url, {'value': '1'})
        res3 = self.client.post(
            self.vote_url,
            {'value': '-1'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(res3.json(), {'score': -1, 'user_vote': -1})
        self.assertEqual(MemeVote.objects.filter(meme=self.meme).count(), 1)

    def test_cannot_vote_on_unpublished_meme(self):
        hidden = Meme.objects.create(
            author=self.user,
            image=make_image_file('hidden.png'),
            is_published=False,
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('memes:vote', args=[hidden.pk]),
            {'value': '1'},
        )
        self.assertEqual(response.status_code, 404)

    def test_author_can_delete_own_meme(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('memes:delete', args=[self.meme.pk]),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Meme.objects.filter(pk=self.meme.pk).exists())
        self.assertContains(response, 'Мем удалён')

    def test_other_user_cannot_delete_meme(self):
        stranger = User.objects.create_user(username='stranger')
        self.client.force_login(stranger)
        response = self.client.post(
            reverse('memes:delete', args=[self.meme.pk]),
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Meme.objects.filter(pk=self.meme.pk).exists())
