from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Permite acessar dicionários dentro do template: dict|get_item:key"""
    return dictionary.get(key)
