# Generated by Django 5.1.4 on 2025-02-11 13:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_defaultshelftype'),
    ]

    operations = [
        migrations.CreateModel(
            name='VideoItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(blank=True, max_length=200, null=True, verbose_name='Título')),
                ('url', models.URLField(verbose_name='URL do Vídeo')),
                ('thumbnail', models.ImageField(blank=True, upload_to='videos/thumbnails/', verbose_name='Thumbnail')),
                ('ordem', models.IntegerField(default=0, verbose_name='Ordem')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
            ],
            options={
                'verbose_name': 'Vídeo',
                'verbose_name_plural': 'Vídeos',
                'ordering': ['ordem'],
            },
        ),
        migrations.RemoveField(
            model_name='videosection',
            name='ordem',
        ),
        migrations.RemoveField(
            model_name='videosection',
            name='thumbnail',
        ),
        migrations.RemoveField(
            model_name='videosection',
            name='url',
        ),
        migrations.CreateModel(
            name='VideoSectionItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ordem', models.IntegerField(default=0, verbose_name='Ordem')),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.videoitem')),
                ('video_section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.videosection')),
            ],
            options={
                'verbose_name': 'Item de Vídeo',
                'verbose_name_plural': 'Itens de Vídeo',
                'ordering': ['ordem', '-added_at'],
                'unique_together': {('video_section', 'video')},
            },
        ),
        migrations.AddField(
            model_name='videosection',
            name='videos',
            field=models.ManyToManyField(related_name='sections', through='core.VideoSectionItem', to='core.videoitem', verbose_name='Vídeos'),
        ),
    ]
