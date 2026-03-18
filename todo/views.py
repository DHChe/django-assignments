from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from todo.models import Todo
from django.http import Http404


def todo_list(request):
    todo_list = Todo.objects.all().values_list("id", "title")
    result = [{"id": todo[0], "title": todo[1]} for i, todo in enumerate(todo_list)]
    return render(request, "todo_list.html", {"data": result})


@login_required
def todo_detail(request, todo_id):
    try:
        todo = Todo.objects.get(id=todo_id)
        info = {
            "title": todo.title,
            "description": todo.description,
            "start_date": todo.start_date,
            "end_date": todo.end_date,
            "is_completed": todo.is_completed,
        }
        return render(request, "todo_detail.html", {"data": info})
    except Todo.DoesNotExist:
        return Http404("할일이 존재하지 않습니다.")




