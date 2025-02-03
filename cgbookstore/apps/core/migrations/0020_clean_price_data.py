from django.db import migrations
from django.db.migrations.operations.special import RunSQL

class Migration(migrations.Migration):
    """
    Migração para limpar dados incorretos dos campos de preço usando SQL direto
    """
    dependencies = [
        ('core', '0019_update_price_structure'),
    ]

    operations = [
        RunSQL(
            # SQL para limpar os dados
            sql="""
            UPDATE core_book 
            SET preco = NULL, 
                preco_promocional = NULL 
            WHERE preco LIKE '{%' 
               OR preco = '{}' 
               OR preco IS NOT NULL;
            """,
            # SQL de reversão (não faz nada)
            reverse_sql="""
            SELECT 1;
            """
        ),
    ]