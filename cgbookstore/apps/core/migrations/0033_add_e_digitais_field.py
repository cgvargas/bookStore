from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0032_add_shelf_type_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='e_digitais',
            field=models.BooleanField(
                verbose_name='É Livro Digital',
                default=False,
                help_text='Marque se este livro está disponível em formato digital'
            ),
        ),
    ]