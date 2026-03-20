from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AuthenticationJourneyTests(TestCase):
    def test_signup_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "new-user",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, settings.LOGIN_URL)
        self.assertTrue(User.objects.filter(username="new-user").exists())

    def test_signup_rejects_password_confirmation_mismatch(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "invalid-user",
                "password1": "StrongPass123!",
                "password2": "DifferentPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertFalse(User.objects.filter(username="invalid-user").exists())

    def test_login_redirects_to_todo_list_when_credentials_are_valid(self):
        user = User.objects.create_user(
            username="member",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "member",
                "password": "StrongPass123!",
            },
        )

        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)
        self.assertEqual(self.client.session.get("_auth_user_id"), str(user.pk))

    def test_login_shows_error_when_credentials_are_invalid(self):
        User.objects.create_user(
            username="member",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "member",
                "password": "WrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertIsNone(self.client.session.get("_auth_user_id"))
