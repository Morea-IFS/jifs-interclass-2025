# app/templatetags/sticker_extras.py
from django import template
from django.core.serializers.json import DjangoJSONEncoder
import json
register = template.Library()

@register.filter
def template_to_json(t):
    data = {
        'id': t.id, 'name': t.name, 'event': t.event_id or '',
        'image': t.base_image.url, 'width': t.width_mm, 'height': t.height_mm,
        'px': t.photo_x, 'py': t.photo_y, 'pw': t.photo_width, 'ph': t.photo_height,
        'radius': t.photo_corner_radius,
        'shown': t.show_name, 'ny': t.name_y, 'fontsize': t.name_font_size, 'color': t.name_color,
        'show_campus': t.show_campus, 'campus_side': t.campus_side,
        'show_year': t.show_year, 'year_side': t.year_side,
        'side_font_size': t.side_font_size, 'side_color': t.side_color,
        'active': t.active, 'default': t.is_default,
    }
    return json.dumps(data, cls=DjangoJSONEncoder)