#!/usr/bin/env python
import os
import sys
import django
from django.db import transaction

# Configurar o ambiente Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cgbookstore.config.settings")
django.setup()

from cgbookstore.apps.core.models.home_content import (
    HomeSection,
    BookShelfSection,
    DefaultShelfType,
    BookShelfItem
)
from cgbookstore.apps.core.models.book import Book

def fix_shelf_configurations():
    """
    Corrige configurações de prateleiras e tipos de prateleira
    """
    print("=" * 80)
    print("🔧 CORREÇÃO DE CONFIGURAÇÕES DE PRATELEIRAS 🔧")
    print("=" * 80)

    # 1. Corrigir tipos de prateleira problemáticos
    problematic_shelf_types = [
        {
            'identificador': 'livros_digitais',
            'nome': 'eBooks',
            'filtro_campo': 'e_digitais',
            'filtro_valor': 'True'
        },
        {
            'identificador': 'e_mais_vendidos',
            'nome': 'Mais Vendidos',
            'filtro_campo': 'quantidade_vendida__gt',
            'filtro_valor': '0'
        }
    ]

    with transaction.atomic():
        for shelf_type_data in problematic_shelf_types:
            shelf_type, created = DefaultShelfType.objects.get_or_create(
                identificador=shelf_type_data['identificador'],
                defaults={
                    'nome': shelf_type_data['nome'],
                    'filtro_campo': shelf_type_data['filtro_campo'],
                    'filtro_valor': shelf_type_data['filtro_valor'],
                    'ativo': True,
                    'ordem': 0
                }
            )

            if created:
                print(f"✅ Criado tipo de prateleira: {shelf_type.nome}")
            else:
                print(f"ℹ️ Tipo de prateleira já existente: {shelf_type.nome}")

    # 2. Corrigir seções de home sem prateleira
    home_sections_to_fix = [
        {
            'titulo': 'eBooks',
            'tipo': 'shelf',
            'ordem': 3,
            'shelf_type': DefaultShelfType.objects.get(identificador='livros_digitais')
        },
        {
            'titulo': 'Mais Vendidos',
            'tipo': 'shelf',
            'ordem': 4,
            'shelf_type': DefaultShelfType.objects.get(identificador='e_mais_vendidos')
        }
    ]

    for section_data in home_sections_to_fix:
        # Criar ou atualizar seção de home
        home_section, section_created = HomeSection.objects.get_or_create(
            titulo=section_data['titulo'],
            defaults={
                'tipo': section_data['tipo'],
                'ativo': True,
                'ordem': section_data['ordem']
            }
        )

        # Criar ou atualizar prateleira
        book_shelf, shelf_created = BookShelfSection.objects.get_or_create(
            section=home_section,
            defaults={
                'shelf_type': section_data['shelf_type'],
                'max_livros': 12,
                'tipo_shelf': 'custom'
            }
        )

        if section_created:
            print(f"✅ Seção de home criada: {home_section.titulo}")
        if shelf_created:
            print(f"✅ Prateleira criada para seção: {home_section.titulo}")

    # 3. Corrigir prateleira "Padrão"
    try:
        default_section = HomeSection.objects.get(titulo='Padrão')
        default_shelf_type, _ = DefaultShelfType.objects.get_or_create(
            identificador='default',
            defaults={
                'nome': 'Padrão',
                'filtro_campo': 'quantidade_vendida__gt',
                'filtro_valor': '0',
                'ativo': True,
                'ordem': 0
            }
        )

        # Atualizar prateleira padrão
        default_book_shelf, _ = BookShelfSection.objects.get_or_create(
            section=default_section,
            defaults={
                'shelf_type': default_shelf_type,
                'max_livros': 12,
                'tipo_shelf': 'bestsellers'
            }
        )

        print("✅ Prateleira Padrão corrigida")
    except Exception as e:
        print(f"❌ Erro ao corrigir prateleira Padrão: {e}")

def main():
    try:
        fix_shelf_configurations()
    except Exception as e:
        print(f"❌ Erro durante a correção: {e}")

if __name__ == '__main__':
    main()