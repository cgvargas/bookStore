from django.db import migrations, models
from django.utils import timezone


def remove_duplicates(apps, schema_editor):
    UserBookShelf = apps.get_model('core', 'UserBookShelf')
    seen = set()
    to_delete = []

    for shelf in UserBookShelf.objects.all():
        pair = (shelf.user_id, shelf.book_id)
        if pair in seen:
            to_delete.append(shelf.id)
        else:
            seen.add(pair)

    if to_delete:
        UserBookShelf.objects.filter(id__in=to_delete).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0007_user_email_verification_token_user_email_verified'),
    ]

    operations = [
        # Primeiro remove duplicados
        migrations.RunPython(remove_duplicates),

        # Depois adiciona os campos e restrições
        migrations.AlterModelOptions(
            name='userbookshelf',
            options={'ordering': ['-added_at'], 'verbose_name': 'Prateleira de Usuário',
                     'verbose_name_plural': 'Prateleiras de Usuários'},
        ),
        migrations.AddField(
            model_name='book',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=timezone.now, verbose_name='Criado em'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='book',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Atualizado em'),
        ),
        migrations.AddField(
            model_name='userbookshelf',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Atualizado em'),
        ),
        migrations.AlterField(
            model_name='book',
            name='categoria',
            field=models.CharField(default='', max_length=100, verbose_name='Categoria'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='book',
            name='editora',
            field=models.CharField(default='', max_length=100, verbose_name='Editora'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='userbookshelf',
            unique_together={('user', 'book')},
        ),
    ]