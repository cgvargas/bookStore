import os
import django
from pathlib import Path

# Configurar ambiente Django
project_dir = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from django.apps import apps


def recreate_content_types():
    print("Recriando tabela de content types...")

    # Remover todos os content types existentes
    ContentType.objects.all().delete()

    # Criar novos content types para cada modelo
    created_count = 0
    for app_config in apps.get_app_configs():
        print(f"Processando app: {app_config.label}")

        for model in app_config.get_models():
            try:
                content_type, created = ContentType.objects.get_or_create(
                    app_label=app_config.label,
                    model=model._meta.model_name
                )
                if created:
                    created_count += 1
                    print(f"  ✓ Content type criado: {content_type.app_label}.{content_type.model}")
            except Exception as e:
                print(f"  ✗ Erro ao criar content type para {model._meta.model_name}: {str(e)}")

    print(f"\nTotal de {created_count} content types criados!")


if __name__ == "__main__":
    recreate_content_types()