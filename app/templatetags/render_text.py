# templatetags/render_text.py
from django import template
from django.template import Template, Context
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def render_with_user(text, user):
    if not text:
        return ''
    try:
        t = Template(text)
        c = Context({'user': user})
        return mark_safe(t.render(c))
    except Exception:
        return text  # se houver erro na sintaxe, retorna o texto bruto