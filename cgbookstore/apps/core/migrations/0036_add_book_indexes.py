# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_customsectiontype_alter_book_tipo_shelf_especial_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='book',
            index=models.Index(fields=['tipo_shelf_especial'], name='idx_book_shelf_especial'),
        ),
        migrations.AddIndex(
            model_name='book',
            index=models.Index(fields=['e_destaque'], name='idx_book_destaque'),
        ),
        migrations.AddIndex(
            model_name='book',
            index=models.Index(fields=['e_lancamento'], name='idx_book_lancamento'),
        ),
        migrations.AddIndex(
            model_name='book',
            index=models.Index(fields=['quantidade_vendida'], name='idx_book_vendas'),
        ),
        migrations.AddIndex(
            model_name='book',
            index=models.Index(fields=['quantidade_acessos'], name='idx_book_acessos'),
        ),
        migrations.AddIndex(
            model_name='book',
            index=models.Index(fields=['external_id'], name='idx_book_external'),
        ),
    ]