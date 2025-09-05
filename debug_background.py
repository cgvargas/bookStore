#!/usr/bin/env python
"""
Script de debug para verificar configurações de background
Uso: python debug_background.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()

from cgbookstore.apps.core.models.home_content import HomeSection, BackgroundSettings


def debug_background():
    print("🔍 DEBUG: Verificando configurações de background")
    print("=" * 60)

    # 1. Verificar se existem seções do tipo background
    background_sections = HomeSection.objects.filter(tipo='background')
    print(f"📊 Total de seções 'background': {background_sections.count()}")

    if background_sections.exists():
        for i, section in enumerate(background_sections, 1):
            print(f"\n📋 Seção {i}:")
            print(f"   - ID: {section.id}")
            print(f"   - Título: {section.titulo}")
            print(f"   - Ativo: {section.ativo}")
            print(f"   - Ordem: {section.ordem}")
            print(f"   - Tem background_settings: {hasattr(section, 'background_settings')}")

            if hasattr(section, 'background_settings'):
                bg = section.background_settings
                print(f"   - Background habilitado: {bg.habilitado}")
                print(f"   - Imagem: {bg.imagem}")
                print(f"   - URL da imagem: {bg.imagem.url if bg.imagem else 'Nenhuma'}")
                print(f"   - Opacidade: {bg.opacidade}")
                print(f"   - Aplicar em: {bg.aplicar_em}")
                print(f"   - Posição: {bg.posicao}")
            else:
                print("   ❌ background_settings não existe!")
    else:
        print("   ❌ Nenhuma seção do tipo 'background' encontrada!")

    # 2. Verificar BackgroundSettings órfãos
    print(f"\n🔍 BackgroundSettings no total: {BackgroundSettings.objects.count()}")
    for bg in BackgroundSettings.objects.all():
        print(f"   - ID: {bg.id}, Seção: {bg.section.titulo if bg.section else 'SEM SEÇÃO'}")

    # 3. Verificar seções ativas na ordem
    print(f"\n📈 Todas as seções ativas ordenadas:")
    active_sections = HomeSection.objects.filter(ativo=True).order_by('ordem')
    for section in active_sections:
        icon = "🎨" if section.tipo == 'background' else "📚" if section.tipo == 'shelf' else "🎥" if section.tipo == 'video' else "👤" if section.tipo == 'author' else "📋"
        print(f"   {section.ordem}: {icon} {section.titulo} ({section.get_tipo_display()})")

    print("=" * 60)
    print("✅ Verificação concluída!")

    # 4. Se não existir nenhuma seção background, sugerir criação
    if not background_sections.exists():
        print("\n🛠️  NENHUMA seção background encontrada!")
        print("Para criar uma seção de background, execute no Django Admin:")
        print("1. Vá para 'Home Sections'")
        print("2. Clique em 'Adicionar'")
        print("3. Preencha:")
        print("   - Título: 'Imagem de Fundo do Site'")
        print("   - Tipo: 'Imagem de Fundo do Site'")
        print("   - Ordem: 0")
        print("   - Ativo: ✓")
        print("4. Salve")
        print("5. Depois, vá para 'Background Settings' e crie as configurações")


if __name__ == '__main__':
    debug_background()