# Generated by Django 5.1.4 on 2025-02-17 11:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_videosectionitem_ativo'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='password_history',
            field=models.JSONField(blank=True, default=list, verbose_name='Histórico de Senhas'),
        ),
    ]
