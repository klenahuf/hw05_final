from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from http import HTTPStatus
from posts.models import Post, Group
from .constants import (
    AUTHOR_USERNAME,
    GROUP_SLUG,
    URL_INDEX,
    URL_GROUP,
    URL_AUTHOR_PROFILE,
    URL_CREATE_POST,
)

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.user = User.objects.create_user(username="some_user")

        cls.group = Group.objects.create(
            title="группа",
            slug=GROUP_SLUG,
            description="проверка описания"
        )
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=cls.author_user,
            group=cls.group
        )
        cls.POST_URL = reverse("posts:post_detail", args=[cls.post.id])
        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])
        cls.URL_TO_TEMPLATE = {
            URL_INDEX: "posts/index.html",
            URL_GROUP: "posts/group_list.html",
            URL_AUTHOR_PROFILE: "posts/profile.html",
            PostURLTests.POST_URL: "posts/post_detail.html",
            PostURLTests.POST_EDIT_URL: "posts/create_post.html",
            URL_CREATE_POST: "posts/create_post.html",
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.author_user)

    def test_urls_status(self):
        address_status_client = [
            [URL_INDEX, HTTPStatus.OK, self.guest_client],
            [URL_GROUP, HTTPStatus.OK, self.guest_client],
            [URL_AUTHOR_PROFILE, HTTPStatus.OK, self.guest_client],
            [URL_CREATE_POST, HTTPStatus.OK, self.authorized_client],
            [URL_CREATE_POST, HTTPStatus.FOUND, self.guest_client],
            [PostURLTests.POST_URL, HTTPStatus.OK, self.guest_client],
            [PostURLTests.POST_EDIT_URL, HTTPStatus.FOUND, self.guest_client],
            [
                PostURLTests.POST_EDIT_URL,
                HTTPStatus.FOUND,
                self.authorized_client,
            ],
            [PostURLTests.POST_EDIT_URL, HTTPStatus.OK, self.author_client],
        ]
        for test in address_status_client:
            adress, status, client = test
            with self.subTest(test=test):
                self.assertEqual(
                    client.get(adress).status_code,
                    status,
                )

    def test_task_list_url_redirect_anonymous(self):
        response = self.authorized_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        for url, template in PostURLTests.URL_TO_TEMPLATE.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(
                    response,
                    template,
                )

    def test_post_urls_redirects_correct(self):
        address_redirect_client = [
            [
                URL_CREATE_POST,
                f"/auth/login/?next={URL_CREATE_POST}",
                self.guest_client,
            ],
            [
                PostURLTests.POST_EDIT_URL,
                f"/auth/login/?next={PostURLTests.POST_EDIT_URL}",
                self.guest_client,
            ],
            [
                PostURLTests.POST_EDIT_URL,
                PostURLTests.POST_URL,
                self.authorized_client,
            ],
        ]
        for url, redirect_address, client in address_redirect_client:
            with self.subTest(url=url, client=client):
                response = client.get(url, follow=True)
                self.assertRedirects(response, redirect_address)
