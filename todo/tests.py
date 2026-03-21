from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from todo.models import Todo


User = get_user_model()


class TodoUserJourneyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username="owner",
            password="StrongPass123!",
        )
        cls.other_user = User.objects.create_user(
            username="other",
            password="StrongPass123!",
        )
        cls.owner_todo = Todo.objects.create(
            title="주간 회의 준비",
            description="발표 자료와 회의록을 정리한다.",
            start_date=date(2026, 3, 19),
            end_date=date(2026, 3, 20),
            user=cls.owner,
        )
        cls.other_todo = Todo.objects.create(
            title="다른 사람 일정",
            description="보이면 안 되는 일정이다.",
            start_date=date(2026, 3, 19),
            end_date=date(2026, 3, 21),
            user=cls.other_user,
        )

    def login(self, *, username="owner", password="StrongPass123!"):
        self.client.login(username=username, password=password)

    def test_anonymous_user_sees_login_prompt_on_todo_list(self):
        response = self.client.get(reverse("todo_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "로그인이 필요합니다")
        self.assertEqual(list(response.context["data"]), [])

    def test_protected_todo_routes_redirect_anonymous_users(self):
        detail_url = reverse("todo_detail", kwargs={"todo_id": self.owner_todo.pk})
        update_url = reverse("todo_update", kwargs={"todo_id": self.owner_todo.pk})
        delete_url = reverse("todo_delete", kwargs={"todo_id": self.owner_todo.pk})

        self.assertRedirects(
            self.client.get(reverse("todo_create")),
            f"{reverse('login')}?next={reverse('todo_create')}",
        )
        self.assertRedirects(
            self.client.get(detail_url),
            f"{reverse('login')}?next={detail_url}",
        )
        self.assertRedirects(
            self.client.get(update_url),
            f"{reverse('login')}?next={update_url}",
        )
        self.assertRedirects(
            self.client.post(delete_url),
            f"{reverse('login')}?next={delete_url}",
        )

    def test_authenticated_user_sees_only_own_todos(self):
        self.login()

        response = self.client.get(reverse("todo_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.owner_todo.title)
        self.assertNotContains(response, self.other_todo.title)

    def test_search_matches_title_and_description_and_handles_empty_result(self):
        self.login()
        Todo.objects.create(
            title="장보기",
            description="우유와 빵을 구매한다.",
            start_date=date(2026, 3, 21),
            end_date=date(2026, 3, 21),
            user=self.owner,
        )

        response = self.client.get(reverse("todo_list"), {"q": "회의록"})
        self.assertContains(response, "주간 회의 준비")
        self.assertNotContains(response, "장보기")

        empty_response = self.client.get(reverse("todo_list"), {"q": "없는 검색어"})
        self.assertContains(empty_response, "All caught up!")
        self.assertEqual(len(empty_response.context["data"]), 0)

    def test_list_supports_pagination_after_ten_items(self):
        self.login()
        for index in range(11):
            Todo.objects.create(
                title=f"페이지 테스트 {index}",
                description="페이지네이션 확인",
                start_date=date(2026, 3, 19) + timedelta(days=index),
                end_date=date(2026, 3, 20) + timedelta(days=index),
                user=self.owner,
            )

        response = self.client.get(reverse("todo_list"), {"page": 2})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertEqual(response.context["page_obj"].paginator.num_pages, 2)
        self.assertEqual(len(response.context["data"]), 2)

    def test_owner_can_view_todo_detail(self):
        self.login()

        response = self.client.get(
            reverse("todo_detail", kwargs={"todo_id": self.owner_todo.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.owner_todo.title)
        self.assertContains(response, "Edit")

    def test_user_cannot_view_another_users_todo_detail(self):
        self.login()

        response = self.client.get(
            reverse("todo_detail", kwargs={"todo_id": self.other_todo.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_valid_create_flow_assigns_logged_in_user_and_redirects_to_detail(self):
        self.login()
        payload = {
            "title": "새로운 할 일",
            "description": "자동화 테스트로 생성한다.",
            "start_date": "2026-03-22",
            "end_date": "2026-03-23",
        }

        response = self.client.post(reverse("todo_create"), payload)

        created_todo = Todo.objects.get(title="새로운 할 일")
        self.assertRedirects(
            response,
            reverse("todo_detail", kwargs={"todo_id": created_todo.pk}),
        )
        self.assertEqual(created_todo.user, self.owner)
        self.assertFalse(created_todo.is_completed)

    def test_create_rejects_missing_fields(self):
        self.login()

        response = self.client.post(
            reverse("todo_create"),
            {
                "title": "",
                "description": "",
                "start_date": "",
                "end_date": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "title", "This field is required.")
        self.assertEqual(Todo.objects.filter(user=self.owner).count(), 1)

    def test_create_rejects_end_date_before_start_date(self):
        self.login()

        response = self.client.post(
            reverse("todo_create"),
            {
                "title": "잘못된 일정",
                "description": "날짜 검증 테스트",
                "start_date": "2026-03-25",
                "end_date": "2026-03-24",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "end_date",
            "종료일은 시작일보다 빠를 수 없습니다.",
        )
        self.assertFalse(Todo.objects.filter(title="잘못된 일정").exists())

    def test_update_page_renders_for_owner(self):
        self.login()

        response = self.client.get(
            reverse("todo_update", kwargs={"todo_id": self.owner_todo.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Task")
        self.assertContains(response, self.owner_todo.title)

    def test_owner_can_update_todo_and_mark_complete(self):
        self.login()

        response = self.client.post(
            reverse("todo_update", kwargs={"todo_id": self.owner_todo.pk}),
            {
                "title": "수정된 할 일",
                "description": "완료 처리까지 반영한다.",
                "start_date": "2026-03-19",
                "end_date": "2026-03-22",
                "is_completed": "on",
            },
        )

        self.owner_todo.refresh_from_db()

        self.assertRedirects(
            response,
            reverse("todo_detail", kwargs={"todo_id": self.owner_todo.pk}),
        )
        self.assertEqual(self.owner_todo.title, "수정된 할 일")
        self.assertTrue(self.owner_todo.is_completed)

    def test_user_cannot_update_another_users_todo(self):
        self.login()

        response = self.client.post(
            reverse("todo_update", kwargs={"todo_id": self.other_todo.pk}),
            {
                "title": "침범 시도",
                "description": "권한 체크",
                "start_date": "2026-03-19",
                "end_date": "2026-03-20",
                "is_completed": "on",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_delete_only_accepts_post(self):
        self.login()

        response = self.client.get(
            reverse("todo_delete", kwargs={"todo_id": self.owner_todo.pk})
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Todo.objects.filter(pk=self.owner_todo.pk).exists())

    def test_owner_can_delete_todo(self):
        self.login()

        response = self.client.post(
            reverse("todo_delete", kwargs={"todo_id": self.owner_todo.pk})
        )

        self.assertRedirects(response, reverse("todo_list"))
        self.assertFalse(Todo.objects.filter(pk=self.owner_todo.pk).exists())

    def test_user_cannot_delete_another_users_todo(self):
        self.login()

        response = self.client.post(
            reverse("todo_delete", kwargs={"todo_id": self.other_todo.pk})
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Todo.objects.filter(pk=self.other_todo.pk).exists())


class TodoCbvJourneyTests(TestCase):
    """CBV routes (`cbv/` prefix, `cbv_todo_*` names)."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username="cbv_owner",
            password="StrongPass123!",
        )
        cls.other_user = User.objects.create_user(
            username="cbv_other",
            password="StrongPass123!",
        )
        cls.superuser = User.objects.create_superuser(
            username="cbv_admin",
            password="StrongPass123!",
            email="admin@example.com",
        )
        cls.owner_todo = Todo.objects.create(
            title="CBV 주간 회의",
            description="회의록 정리",
            start_date=date(2026, 3, 19),
            end_date=date(2026, 3, 20),
            user=cls.owner,
        )
        cls.other_todo = Todo.objects.create(
            title="CBV 타인 일정",
            description="열람 금지",
            start_date=date(2026, 3, 19),
            end_date=date(2026, 3, 21),
            user=cls.other_user,
        )

    def login(self, *, username="cbv_owner", password="StrongPass123!"):
        self.client.login(username=username, password=password)

    def test_protected_cbv_routes_redirect_anonymous_users(self):
        detail_url = reverse("cbv_todo_detail", kwargs={"pk": self.owner_todo.pk})
        update_url = reverse("cbv_todo_update", kwargs={"pk": self.owner_todo.pk})
        delete_url = reverse("cbv_todo_delete", kwargs={"pk": self.owner_todo.pk})

        self.assertRedirects(
            self.client.get(reverse("cbv_todo_list")),
            f"{reverse('login')}?next={reverse('cbv_todo_list')}",
        )
        self.assertRedirects(
            self.client.get(reverse("cbv_todo_create")),
            f"{reverse('login')}?next={reverse('cbv_todo_create')}",
        )
        self.assertRedirects(
            self.client.get(detail_url),
            f"{reverse('login')}?next={detail_url}",
        )
        self.assertRedirects(
            self.client.get(update_url),
            f"{reverse('login')}?next={update_url}",
        )
        self.assertRedirects(
            self.client.get(delete_url),
            f"{reverse('login')}?next={delete_url}",
        )

    def test_authenticated_user_sees_only_own_todos_on_cbv_list(self):
        self.login()

        response = self.client.get(reverse("cbv_todo_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.owner_todo.title)
        self.assertNotContains(response, self.other_todo.title)

    def test_superuser_cbv_list_sees_all_todos(self):
        self.client.login(username="cbv_admin", password="StrongPass123!")

        response = self.client.get(reverse("cbv_todo_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.owner_todo.title)
        self.assertContains(response, self.other_todo.title)

    def test_cbv_search_and_pagination(self):
        self.login()
        Todo.objects.create(
            title="CBV 장보기",
            description="우유 구매",
            start_date=date(2026, 3, 21),
            end_date=date(2026, 3, 21),
            user=self.owner,
        )

        response = self.client.get(reverse("cbv_todo_list"), {"q": "회의록"})
        self.assertContains(response, self.owner_todo.title)
        self.assertNotContains(response, "CBV 장보기")

        for index in range(11):
            Todo.objects.create(
                title=f"CBV 페이지 {index}",
                description="paginate",
                start_date=date(2026, 3, 19) + timedelta(days=index),
                end_date=date(2026, 3, 20) + timedelta(days=index),
                user=self.owner,
            )

        page2 = self.client.get(reverse("cbv_todo_list"), {"page": 2})
        self.assertEqual(page2.status_code, 200)
        self.assertEqual(page2.context["page_obj"].number, 2)

    def test_owner_can_view_cbv_detail(self):
        self.login()

        response = self.client.get(
            reverse("cbv_todo_detail", kwargs={"pk": self.owner_todo.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.owner_todo.title)

    def test_user_cannot_view_another_users_cbv_detail(self):
        self.login()

        response = self.client.get(
            reverse("cbv_todo_detail", kwargs={"pk": self.other_todo.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_valid_cbv_create_redirects_to_cbv_detail(self):
        self.login()
        payload = {
            "title": "CBV 신규",
            "description": "생성 테스트",
            "start_date": "2026-03-22",
            "end_date": "2026-03-23",
        }

        response = self.client.post(reverse("cbv_todo_create"), payload)

        created = Todo.objects.get(title="CBV 신규")
        self.assertRedirects(
            response,
            reverse("cbv_todo_detail", kwargs={"pk": created.pk}),
        )
        self.assertEqual(created.user, self.owner)

    def test_cbv_update_redirects_to_cbv_detail(self):
        self.login()

        response = self.client.post(
            reverse("cbv_todo_update", kwargs={"pk": self.owner_todo.pk}),
            {
                "title": "CBV 수정됨",
                "description": "업데이트",
                "start_date": "2026-03-19",
                "end_date": "2026-03-22",
                "is_completed": "on",
            },
        )

        self.owner_todo.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("cbv_todo_detail", kwargs={"pk": self.owner_todo.pk}),
        )
        self.assertEqual(self.owner_todo.title, "CBV 수정됨")
        self.assertTrue(self.owner_todo.is_completed)

    def test_user_cannot_update_another_users_cbv_todo(self):
        self.login()

        response = self.client.post(
            reverse("cbv_todo_update", kwargs={"pk": self.other_todo.pk}),
            {
                "title": "침범",
                "description": "x",
                "start_date": "2026-03-19",
                "end_date": "2026-03-20",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_cbv_delete_get_renders_confirmation(self):
        self.login()

        response = self.client.get(
            reverse("cbv_todo_delete", kwargs={"pk": self.owner_todo.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "할 일 삭제")

    def test_cbv_delete_post_redirects_to_cbv_list(self):
        self.login()

        response = self.client.post(
            reverse("cbv_todo_delete", kwargs={"pk": self.owner_todo.pk})
        )

        self.assertRedirects(response, reverse("cbv_todo_list"))
        self.assertFalse(Todo.objects.filter(pk=self.owner_todo.pk).exists())

    def test_user_cannot_delete_another_users_cbv_todo(self):
        self.login()

        response = self.client.post(
            reverse("cbv_todo_delete", kwargs={"pk": self.other_todo.pk})
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Todo.objects.filter(pk=self.other_todo.pk).exists())
