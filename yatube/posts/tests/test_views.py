import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from ..models import Group, Post, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.USER_NAME = 'test_user'
        cls.GROUP_TITLE = 'Тестовая группа'
        cls.GROUP_SLUG = 'test_group_slug'
        cls.GROUP_2_SLUG = 'test_group_slug_2'

        cls.POST_TEXT = 'Тестовый пост'

        cls.user = User.objects.create_user(username=cls.USER_NAME)
        cls.followed_user = User.objects.create_user(username='follower')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=cls.GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug=cls.GROUP_2_SLUG,
            description='Тестовое описание 2',
        )

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text=cls.POST_TEXT,
            group=cls.group,
            image=SimpleUploadedFile(
                name='small.gif',
                content=cls.small_gif,
                content_type='image/gif'
            )
        )
        cls.image = cls.post.image
        cls.post_id = cls.post.id

        cls.follow = Follow.objects.create(
            user=cls.followed_user,
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def post_obj_test_correct_context(self, post_obj):
        self.assertEqual(post_obj.pk, self.post_id)
        self.assertEqual(post_obj.author, self.user)
        self.assertEqual(post_obj.text, self.POST_TEXT)
        self.assertEqual(post_obj.group, self.group)
        self.assertEqual(post_obj.image, self.image)

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.GROUP_SLUG}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.USER_NAME}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post_id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post_id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(
            response.context.get('title'),
            'Последние обновления на сайте'
        )
        self.assertEqual(response.context.get('index'), True)
        self.post_obj_test_correct_context(response.context.get('page_obj')[0])

    def test_group_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.GROUP_SLUG})
        )

        self.assertEqual(
            response.context.get('title'),
            f'Записи сообщества "{self.GROUP_TITLE}"'
        )
        self.assertEqual(response.context.get('group'), self.group)
        self.post_obj_test_correct_context(response.context.get('page_obj')[0])

    def test_group_show_own_posts(self):
        """ Проверка, что на страницу группы без постов не попали посты """
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.GROUP_2_SLUG})
        )

        self.assertEqual(len(response.context.get('page_obj')), 0)

    def test_profile_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )

        self.assertEqual(response.context.get('author'), self.user)
        self.assertEqual(response.context.get('author_posts_count'), 1)
        self.post_obj_test_correct_context(response.context.get('page_obj')[0])

    def test_post_detail_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post_id})
        )

        self.post_obj_test_correct_context(response.context.get('post'))
        self.assertEqual(response.context.get('author_posts_count'), 1)

    def test_post_edit_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post_id})
        )

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_follow_index_follower_client(self):
        follower_client = Client()
        follower_client.force_login(self.followed_user)
        response = follower_client.get(reverse(
            'posts:follow_index'
        ))
        follower_posts_count = len(response.context['page_obj'])
        self.assertEqual(follower_posts_count, 1)

    def test_follow_index_not_follower_client(self):
        response = self.authorized_client.get(reverse(
            'posts:follow_index'
        ))
        follower_posts_count = len(response.context['page_obj'])
        self.assertEqual(follower_posts_count, 0)


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.USER_NAME = 'test_user'
        cls.GROUP_TITLE = 'Тестовая группа'
        cls.GROUP_SLUG = 'test_group_slug'
        cls.POST_TEXT = 'Тестовый пост'

        cls.user = User.objects.create_user(username=cls.USER_NAME)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=cls.GROUP_SLUG,
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text=cls.POST_TEXT,
            group=cls.group,
        )
        cls.image = cls.post.image
        cls.post_id = cls.post.id
        cache.clear()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_correct_cache(self):
        response = self.authorized_client.get(reverse('posts:index'))
        post_obj = response.context.get('page_obj')[0]
        self.assertEqual(post_obj.pk, self.post_id)
        cache_check = response.content
        Post.objects.get(pk=self.post_id).delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, cache_check)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, cache_check)

    def test_follow_unfollow(self):
        followed_user = User.objects.create_user(username='follower')
        followed_client = Client()
        followed_client.force_login(followed_user)

        self.assertEqual(Follow.objects.count(), 0)

        response = followed_client.post(
            reverse('posts:profile_follow', kwargs={'username': self.user}),
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(Follow.objects.last().user, followed_user)
        self.assertEqual(Follow.objects.last().author, self.user)

        response = followed_client.post(
            reverse('posts:profile_unfollow', kwargs={'username': self.user}),
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(Follow.objects.count(), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.POST_COUNT = 13
        cls.POSTS_ON_PAGE = 10
        cls.GROUP_SLUG = 'test_group_slug'

        cls.user = User.objects.create_user(username='test_user')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=cls.GROUP_SLUG,
            description='Тестовое описание',
        )

        for i in range(cls.POST_COUNT):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group
            )
        cache.clear()

    def test_index_paginator_first_page(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), self.POSTS_ON_PAGE)

    def test_index_paginator_second_page(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            self.POST_COUNT - self.POSTS_ON_PAGE
        )

    def test_group_paginator_first_page(self):
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.GROUP_SLUG})
        )
        self.assertEqual(len(response.context['page_obj']), self.POSTS_ON_PAGE)

    def test_group_paginator_second_page(self):
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.GROUP_SLUG})
            + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']),
            self.POST_COUNT - self.POSTS_ON_PAGE
        )

    def test_profile_paginator_first_page(self):
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(len(response.context['page_obj']), self.POSTS_ON_PAGE)

    def test_profile_paginator_second_page(self):
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
            + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']),
            self.POST_COUNT - self.POSTS_ON_PAGE
        )
