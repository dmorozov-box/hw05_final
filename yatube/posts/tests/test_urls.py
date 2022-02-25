from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Group, Post


User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.INCORRECT_SLUG_URL = 'dfdte4517ipe'
        cls.USERNAME = 'test_user'
        cls.GROUP_SLUG = 'test_slug'

        cls.user = User.objects.create_user(username=cls.USERNAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=cls.GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )
        cls.post_id = cls.post.id

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_non_autorised_client(self):
        urls_with_httpstatus = {
            '/': HTTPStatus.OK,
            f'/group/{self.GROUP_SLUG}/': HTTPStatus.OK,
            f'/profile/{self.USERNAME}/': HTTPStatus.OK,
            f'/posts/{self.post_id}/': HTTPStatus.OK,
            f'/group/{self.INCORRECT_SLUG_URL}/': HTTPStatus.NOT_FOUND,
            f'/profile/{self.INCORRECT_SLUG_URL}/': HTTPStatus.NOT_FOUND,
            f'/posts/{self.INCORRECT_SLUG_URL}/': HTTPStatus.NOT_FOUND,
        }
        for address, httpstatus in urls_with_httpstatus.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, httpstatus)

    def test_urls_autorised_client(self):
        urls_with_httpstatus = {
            f'/posts/{self.post_id}/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            f'/posts/{self.INCORRECT_SLUG_URL}/edit/': HTTPStatus.NOT_FOUND,
        }
        for address, httpstatus in urls_with_httpstatus.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, httpstatus)

    def test_create_url_redirect(self):
        response = self.client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_id_edit_url_redirect(self):
        response = self.client.get(
            f'/posts/{self.post_id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post_id}/edit/'
        )

    def test_urls_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.GROUP_SLUG}/': 'posts/group_list.html',
            f'/profile/{self.USERNAME}/': 'posts/profile.html',
            f'/posts/{self.post_id}/': 'posts/post_detail.html',
            f'/posts/{self.post_id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
