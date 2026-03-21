from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import Http404
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from todo.models import Todo


def _user_can_access_todo(user, todo):
    return user.is_superuser or todo.user_id == user.pk


class TodoListView(LoginRequiredMixin, ListView):
    model = Todo
    context_object_name = "data"
    template_name = "todo_list.html"
    paginate_by = 10
    ordering = ("-created_at",)

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            qs = Todo.objects.all()
        else:
            qs = Todo.objects.filter(user=user)

        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        return context


class TodoDetailView(LoginRequiredMixin, DetailView):
    model = Todo
    context_object_name = "data"
    template_name = "todo_info.html"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _user_can_access_todo(self.request.user, obj):
            raise Http404()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.object.__dict__)
        return context


class TodoCreateView(LoginRequiredMixin, CreateView):
    model = Todo
    fields = ("title", "description", "start_date", "end_date")
    template_name = "todo/todo_create.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("cbv_todo_detail", kwargs={"pk": self.object.pk})


class TodoUpdateView(LoginRequiredMixin, UpdateView):
    model = Todo
    fields = ("title", "description", "start_date", "end_date", "is_completed")
    template_name = "todo/todo_update.html"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _user_can_access_todo(self.request.user, obj):
            raise Http404()
        return obj

    def get_success_url(self):
        return reverse("cbv_todo_detail", kwargs={"pk": self.object.pk})


class TodoDeleteView(LoginRequiredMixin, DeleteView):
    model = Todo
    template_name = "todo/todo_confirm_delete.html"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _user_can_access_todo(self.request.user, obj):
            raise Http404()
        return obj

    def get_success_url(self):
        return reverse("cbv_todo_list")
