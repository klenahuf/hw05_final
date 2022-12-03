from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, TEXT_LIMIT
from .constants import AUTHOR_USERNAME, GROUP_SLUG

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.post = Post.objects.create(
            text="Тестовый текст больше 15 символов для проверки...",
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug=GROUP_SLUG,
            description="Тестовое описание",
        )

    def setUp(self):
        self.post = PostModelTest.post
        self.group = PostModelTest.group

    def test_models_str(self):
        vals = (
            (str(self.post), self.post.text[:TEXT_LIMIT]),
            (str(self.group), self.group.title),
        )
        for value, expected in vals:
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_verbose_name(self):
        post = PostModelTest.post
        field_verboses = [
            ("text", "Текст поста"),
            ("pub_date", "Дата публикации"),
            ("author", "Автор"),
            ("group", "Группа"),
        ]
        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        post = PostModelTest.post
        field_help_texts = [
            ("text", "Введите текст поста"),
            ("group", "Выберите группу"),
        ]
        for field, expected_value in field_help_texts:
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value
                )
