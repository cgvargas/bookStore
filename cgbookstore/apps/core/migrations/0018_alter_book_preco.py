# Generated by Django 5.1.4 on 2025-01-29 21:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_book_preco_promocional'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='preco',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Preço'),
        ),
    ]
