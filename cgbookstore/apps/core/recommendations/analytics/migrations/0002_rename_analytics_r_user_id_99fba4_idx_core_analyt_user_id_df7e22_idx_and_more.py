# Generated by Django 5.1.4 on 2025-02-04 11:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core_analytics', '0001_create_recommendation_interaction'),
    ]

    operations = [
        migrations.RenameIndex(
            model_name='recommendationinteraction',
            new_name='core_analyt_user_id_df7e22_idx',
            old_name='analytics_r_user_id_99fba4_idx',
        ),
        migrations.RenameIndex(
            model_name='recommendationinteraction',
            new_name='core_analyt_interac_0e57ff_idx',
            old_name='analytics_r_interac_f0eea9_idx',
        ),
        migrations.RenameIndex(
            model_name='recommendationinteraction',
            new_name='core_analyt_source_731af5_idx',
            old_name='analytics_r_source_eceee3_idx',
        ),
    ]
