from django.db import migrations, models
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_clean_price_data'),  # ajuste o nome da última migração aqui
    ]

    operations = [
        migrations.CreateModel(
            name='RecommendationInteraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interaction_type', models.CharField(choices=[('view', 'Visualização'), ('click', 'Clique'), ('add_shelf', 'Adicionado à Prateleira'), ('purchase', 'Compra'), ('ignore', 'Ignorado')], max_length=20)),
                ('source', models.CharField(choices=[('general', 'Recomendações Gerais'), ('history', 'Baseado no Histórico'), ('category', 'Baseado em Categoria'), ('similarity', 'Similaridade')], max_length=20)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('recommendation_score', models.FloatField(blank=True, null=True)),
                ('position', models.IntegerField(blank=True, null=True)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommendation_interactions', to='core.book')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommendation_interactions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name='recommendationinteraction',
            index=models.Index(fields=['user', 'timestamp'], name='core_recomm_user_id_0c7d6c_idx'),
        ),
        migrations.AddIndex(
            model_name='recommendationinteraction',
            index=models.Index(fields=['interaction_type'], name='core_recomm_interac_99e969_idx'),
        ),
        migrations.AddIndex(
            model_name='recommendationinteraction',
            index=models.Index(fields=['source'], name='core_recomm_source_dd8b20_idx'),
        ),
    ]