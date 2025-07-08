# cgbookstore/apps/chatbot_literario/templatetags/chatbot_filters.py
from django import template
import json

register = template.Library()

@register.filter
def replace(value, arg):
    """Substitui todas as ocorrências de `arg` em `value`."""
    old, new = arg.split(',')
    return value.replace(old, new)

@register.filter
def pprint(value):
    """Formata um dicionário/lista para exibição bonita."""
    try:
        return json.dumps(value, indent=2, ensure_ascii=False)
    except (TypeError, ValueError):
        return value