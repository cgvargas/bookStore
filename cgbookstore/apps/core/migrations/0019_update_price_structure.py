# core/migrations/0019_update_price_structure.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0018_alter_book_preco'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='preco',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name='Preço'
            ),
        ),
        migrations.AlterField(
            model_name='book',
            name='preco_promocional',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name='Preço Promocional'
            ),
        ),
    ]