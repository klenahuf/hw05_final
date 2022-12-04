import shutil

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from random import randint

from ..models import Group, Post, Follow
from ..utils import POST_PER_PAGE
from .constants import (
    AUTHOR_USERNAME,
    GROUP_SLUG,
    URL_INDEX,
    URL_GROUP,
    URL_AUTHOR_PROFILE,
    URL_CREATE_POST,
    TEST_MEDIA,
)

User = get_user_model()


second_page = randint(1, POST_PER_PAGE)
total_posts = POST_PER_PAGE + second_page


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug=GROUP_SLUG,
            description="Тестовое описание группы",
        )
        image_data = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="image_data.gif",
            content=image_data,
            content_type="image/gif"
        )
        cls.post = Post.objects.create(
            text="Тестовый текст поста",
            author=cls.author_user,
            group=cls.group,
            image=uploaded,
        )
        cls.POST_URL = reverse("posts:post_detail", args=[cls.post.id])
        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA, ignore_errors=True)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(PostPagesTests.author_user)
        cache.clear()

    def check_post_info(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, PostPagesTests.post.text)
            self.assertEqual(post.author, PostPagesTests.post.author)
            self.assertEqual(post.group, PostPagesTests.post.group)
            self.assertEqual(post.pk, PostPagesTests.post.pk)
            self.assertEqual(post.image, PostPagesTests.post.image)

    def test_index_page_show_correct_context(self):
        response = self.author_client.get(URL_INDEX)
        self.check_post_info(response.context["page_obj"][0])

    def test_group_page_show_correct_context(self):
        response = self.author_client.get(URL_GROUP)
        self.assertEqual(response.context['group'], PostPagesTests.post.group)
        self.check_post_info(response.context["page_obj"][0])

    def test_profile_page_show_correct_context(self):
        response = self.author_client.get(URL_AUTHOR_PROFILE)
        self.assertEqual(
            response.context['author'],
            PostPagesTests.post.author)
        self.check_post_info(response.context['page_obj'][0])

    def test_post_detail_show_correct_context(self):
        response = self.author_client.get(PostPagesTests.POST_URL)
        self.check_post_info(response.context["post"])

    def test_create_edit_pages_show_correct_context(self):
        adresses = (URL_CREATE_POST, PostPagesTests.POST_EDIT_URL)
        for adress in adresses:
            with self.subTest(adress=adress):
                response = self.author_client.get(adress)
                self.assertIsInstance(
                    response.context["form"].fields["text"],
                    forms.fields.CharField,
                )
                self.assertIsInstance(
                    response.context["form"].fields["group"],
                    forms.fields.ChoiceField,
                )


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title="Тестовое название группы",
            slug=GROUP_SLUG,
            description="Тестовое описание группы",
        )
        cls.PAGES_WITH_PAGINATOR = [URL_INDEX, URL_GROUP, URL_AUTHOR_PROFILE]
        objs = [
            Post(text=f"Пост #{count}", author=cls.user, group=cls.group)
            for count in range(total_posts)
        ]
        Post.objects.bulk_create(objs)

    def setUp(self):
        self.unauthorized_client = Client()
        cache.clear()

    def test_paginator_on_pages_1(self):
        for reverse_address in PaginatorViewsTest.PAGES_WITH_PAGINATOR:
            with self.subTest(reverse_address=reverse_address):
                self.assertEqual(
                    len(
                        self.unauthorized_client.get(
                            reverse_address
                        ).context.get("page_obj")
                    ),
                    POST_PER_PAGE,
                )

    def test_paginator_on_pages_2(self):
        for reverse_address in PaginatorViewsTest.PAGES_WITH_PAGINATOR:
            with self.subTest(reverse_address=reverse_address + "?page=2"):
                self.assertEqual(
                    len(
                        self.unauthorized_client.get(
                            reverse_address + "?page=2"
                        ).context.get("page_obj")
                    ),
                    second_page,
                )


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.test_post = Post.objects.create(
            author=cls.post_author,
            text="Текстовый пост"
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(CacheTest.post_author)

    def test_cache(self):
        post_cache = Post.objects.create(
            text="Тестовый пост 2",
            author=CacheTest.post_author
        )
        response_before = self.author_client.get(URL_INDEX)
        post_cache.delete()
        response_after = self.author_client.get(URL_INDEX)
        self.assertEqual(response_before.content, response_after.content)
        cache.clear()
        response_after_clear = self.author_client.get(URL_INDEX)
        self.assertNotEqual(
            response_after_clear.content, response_after.content
        )


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.post_author = User.objects.create_user(username=AUTHOR_USERNAME)

    def setUp(self) -> None:
        self.author_client = Client()
        self.author_client.force_login(FollowTest.post_author)

    def test_follow(self):
        user_to_follow = User.objects.create_user(username="user_to_follow")
        before_follow = Follow.objects.count()
        self.author_client.get(
            reverse("posts:profile_follow", args=[user_to_follow])
        )
        self.assertEqual(Follow.objects.count(), before_follow + 1)
        new_follower = Follow.objects.first()
        self.assertEqual(new_follower.author, user_to_follow)
        self.assertEqual(new_follower.user, FollowTest.post_author)

    def test_unfollow(self):
        user_to_follow = User.objects.create_user(username="new_follower")
        Follow.objects.create(
            author=user_to_follow, user=FollowTest.post_author
        )
        before_follow = Follow.objects.count()
        self.author_client.get(
            reverse("posts:profile_unfollow", args=[user_to_follow])
        )
        self.assertEqual(Follow.objects.count(), before_follow - 1)

    def test_follow_index_correct(self):
        user_follower = User.objects.create_user(username="user_follower")
        follower_client = Client()
        follower_client.force_login(user_follower)

        follower_client.get(
            reverse("posts:profile_follow", args=[FollowTest.post_author])
        )
        response_follow = follower_client.get(reverse("posts:follow_index"))
        follow_count_before = len(response_follow.context["page_obj"])
        Post.objects.create(
            text="тестовый пост фолловерам", author=FollowTest.post_author
        )
        response_follow = follower_client.get(reverse("posts:follow_index"))
        self.assertEqual(
            follow_count_before + 1, len(response_follow.context["page_obj"])
        )

    def test_unfollow_index_correct(self):
        user_unfollower = User.objects.create_user(username="user_unfollower")
        unfollower_client = Client()
        unfollower_client.force_login(user_unfollower)

        response_unfollow = unfollower_client.get(
            reverse("posts:follow_index")
        )
        unfollow_count_before = len(response_unfollow.context["page_obj"])
        response_unfollow = unfollower_client.get(
            reverse("posts:follow_index")
        )
        self.assertEqual(
            unfollow_count_before, len(response_unfollow.context["page_obj"])
        )
