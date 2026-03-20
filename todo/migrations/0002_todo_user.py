from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def assign_legacy_todos_to_placeholder_user(apps, schema_editor):
    Todo = apps.get_model("todo", "Todo")
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)
    db_alias = schema_editor.connection.alias

    todos_without_user = Todo.objects.using(db_alias).filter(user__isnull=True)
    if not todos_without_user.exists():
        return

    username = "legacy-owner"
    suffix = 1
    while User.objects.using(db_alias).filter(username=username).exists():
        suffix += 1
        username = f"legacy-owner-{suffix}"

    placeholder_user = User.objects.using(db_alias).create(
        username=username,
        password="!",
    )
    todos_without_user.update(user=placeholder_user)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("todo", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="todo",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(assign_legacy_todos_to_placeholder_user, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="todo",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
