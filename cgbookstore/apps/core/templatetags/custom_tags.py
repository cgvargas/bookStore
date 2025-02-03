from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Filtro para acessar valores de dicionários a partir de uma chave dinâmica no template.
    """
    return dictionary.get(key, "")