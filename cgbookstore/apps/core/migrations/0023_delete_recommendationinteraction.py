# Generated by Django 5.1.4 on 2025-02-04 10:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_rename_core_recomm_user_id_0c7d6c_idx_core_recomm_user_id_019362_idx_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='RecommendationInteraction',
        ),
    ]
