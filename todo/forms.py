from django import forms
from todo.models import Todo


class BaseTodoForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "종료일은 시작일보다 빠를 수 없습니다.")

        return cleaned_data


class TodoForm(BaseTodoForm):
    class Meta:
        model = Todo
        fields = ["title", "description", "start_date", "end_date"]


class TodoUpdateForm(BaseTodoForm):
    class Meta:
        model = Todo
        fields = ["title", "description", "start_date", "end_date", "is_completed"]
