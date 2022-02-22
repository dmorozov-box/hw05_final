from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.USER_NAME = 'test_user'

        cls.POST_TEXT = 'Тестовый пост'
        cls.ADDED_POST_TEXT = 'Добавленный пост'
        cls.EDITED_POST_TEXT = 'Отредактированный пост'

        cls.user = User.objects.create_user(username=cls.USER_NAME)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group_slug',
            description='Тестовое описание',
        )

        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_group_slug_2',
            description='Тестовое описание 2',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text=cls.POST_TEXT,
            group=cls.group
        )
        cls.post_id = cls.post.id

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create_form(self):

        post_count_before = Post.objects.count()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': self.ADDED_POST_TEXT,
            'group': self.group.pk,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.USER_NAME}
        ))
        self.assertEqual(Post.objects.count(), post_count_before + 1)

        post = Post.objects.order_by("id").last()
        self.assertEqual(post.text, self.ADDED_POST_TEXT)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author, self.user)

    def test_post_edit_form(self):
        post_count_before = Post.objects.count()

        form_data = {
            'text': self.EDITED_POST_TEXT,
            'group': self.group_2.pk,
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post_id}),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertEqual(Post.objects.count(), post_count_before)

        post = Post.objects.get(pk=self.post_id)
        self.assertEqual(post.text, self.EDITED_POST_TEXT)
        self.assertEqual(post.group, self.group_2)

    def test_create_comment(self):
        comment_count_before = Comment.objects.count()

        form_data = {
            'text': 'Тестовый комментарий',
        }

        response = self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': self.post_id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post_id})
        )

        self.assertEqual(Comment.objects.count(), comment_count_before + 1)

        comment = Comment.objects.order_by("id").last()
        self.assertTrue(comment.text, 'Тестовый комментарий')

        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post_id})
        )
        comment_in_context = response.context.get('comments')[0]
        self.assertEqual(comment_in_context, comment)

        response = self.client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': self.post_id}
            ),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post_id}/comment/',
        )
