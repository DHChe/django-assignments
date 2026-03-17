from django.contrib import admin
from todo.models import Todo


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "start_date", "end_date", "is_completed")
    list_filter = ("is_completed",)
    search_fields = ("title", "description")
    list_editable = ("is_completed",)
    list_per_page = 10
    list_max_show_all = 100
    list_max_show_all = 100
    ordering = ("start_date",)
    fieldsets = (
        ("Todo Detail", {
            "fields": ("title", "description", "is_completed"),
        }),
        ("Date Range", {
            "fields": ("start_date", "end_date"),
        }),
    )
    