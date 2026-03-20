from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from todo.models import Todo
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from todo.forms import TodoForm, TodoUpdateForm
from django.db.models import Q
from django.views.decorators.http import require_POST


def todo_list(request):
    q = request.GET.get("q", "").strip()
    page_obj = None
    if request.user.is_authenticated:
        todo_queryset = Todo.objects.filter(user=request.user).order_by("created_at")
        if q:
            todo_queryset = todo_queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))
        paginator = Paginator(todo_queryset, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        data = page_obj.object_list
    else:
        data = []

    context = {
        "data": data,
        "page_obj": page_obj,
        "q": q,
    }
    return render(request, "todo_list.html", context)


@login_required
def todo_detail(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, user=request.user)
    context = {"data": todo}
    return render(request, "todo_detail.html", context)


@login_required
def todo_create(request):
    form = TodoForm(request.POST or None)
    if form.is_valid():
        todo = form.save(commit=False)
        todo.user = request.user
        todo.save()
        return redirect(reverse("todo_detail", kwargs={"todo_id": todo.pk}))
    context = {
        "form": form,
    }
    return render(request, "todo/todo_create.html", context)


@login_required
def todo_update(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, user=request.user)
    form = TodoUpdateForm(request.POST or None, instance=todo)
    if form.is_valid():
        form.save()
        return redirect(reverse("todo_detail", kwargs={"todo_id": todo.pk}))
    context = {
        "form": form,
    }
    return render(request, "todo/todo_update.html", context)


@login_required
@require_POST
def todo_delete(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, user=request.user)
    todo.delete()
    return redirect(reverse("todo_list"))
