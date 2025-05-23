# Generated by Django 5.1.4 on 2025-04-14 14:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0042_alter_advertisement_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200, verbose_name='Nome')),
                ('sobrenome', models.CharField(blank=True, max_length=200, verbose_name='Sobrenome')),
                ('slug', models.SlugField(blank=True, max_length=250, unique=True, verbose_name='Slug')),
                ('foto', models.ImageField(blank=True, null=True, upload_to='autores/', verbose_name='Foto')),
                ('biografia', models.TextField(blank=True, verbose_name='Biografia')),
                ('data_nascimento', models.DateField(blank=True, null=True, verbose_name='Data de Nascimento')),
                ('nacionalidade', models.CharField(blank=True, max_length=100, verbose_name='Nacionalidade')),
                ('website', models.URLField(blank=True, verbose_name='Website')),
                ('twitter', models.CharField(blank=True, max_length=100, verbose_name='Twitter')),
                ('instagram', models.CharField(blank=True, max_length=100, verbose_name='Instagram')),
                ('facebook', models.CharField(blank=True, max_length=100, verbose_name='Facebook')),
                ('destaque', models.BooleanField(default=False, verbose_name='Destaque')),
                ('ordem', models.IntegerField(default=0, verbose_name='Ordem')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
            ],
            options={
                'verbose_name': 'Autor',
                'verbose_name_plural': 'Autores',
                'ordering': ['nome', 'sobrenome'],
            },
        ),
        migrations.CreateModel(
            name='AuthorSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo_secundario', models.CharField(blank=True, max_length=200, verbose_name='Subtítulo')),
                ('descricao', models.TextField(blank=True, verbose_name='Descrição da Seção')),
                ('mostrar_biografia', models.BooleanField(default=True, verbose_name='Mostrar Biografia')),
                ('apenas_destaque', models.BooleanField(default=False, verbose_name='Apenas Autores em Destaque')),
                ('max_autores', models.IntegerField(default=4, verbose_name='Máximo de Autores')),
                ('ordem_exibicao', models.CharField(choices=[('nome', 'Nome'), ('livros', 'Quantidade de Livros'), ('recentes', 'Mais Recentes'), ('manual', 'Ordem Manual')], default='nome', max_length=20, verbose_name='Ordenar por')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('section', models.OneToOneField(limit_choices_to={'tipo': 'custom'}, on_delete=django.db.models.deletion.CASCADE, related_name='author_section', to='core.homesection', verbose_name='Seção')),
            ],
            options={
                'verbose_name': 'Seção de Autores',
                'verbose_name_plural': 'Seções de Autores',
            },
        ),
        migrations.CreateModel(
            name='AuthorSectionItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ordem', models.IntegerField(default=0, verbose_name='Ordem')),
                ('added_at', models.DateTimeField(auto_now_add=True, verbose_name='Adicionado em')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.author', verbose_name='Autor')),
                ('author_section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.authorsection', verbose_name='Seção de Autores')),
            ],
            options={
                'verbose_name': 'Item de Autor',
                'verbose_name_plural': 'Itens de Autor',
                'ordering': ['ordem', '-added_at'],
                'unique_together': {('author_section', 'author')},
            },
        ),
        migrations.AddField(
            model_name='authorsection',
            name='autores',
            field=models.ManyToManyField(related_name='sections', through='core.AuthorSectionItem', to='core.author', verbose_name='Autores'),
        ),
        migrations.CreateModel(
            name='BookAuthor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(blank=True, help_text='Ex: Autor principal, Co-autor, Editor, etc.', max_length=100, verbose_name='Função')),
                ('is_primary', models.BooleanField(default=False, verbose_name='Autor Principal')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.author', verbose_name='Autor')),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.book', verbose_name='Livro')),
            ],
            options={
                'verbose_name': 'Autor do Livro',
                'verbose_name_plural': 'Autores dos Livros',
                'ordering': ['is_primary', 'id'],
                'unique_together': {('book', 'author')},
            },
        ),
        migrations.AddField(
            model_name='book',
            name='authors',
            field=models.ManyToManyField(related_name='books', through='core.BookAuthor', to='core.author', verbose_name='Autores'),
        ),
    ]
