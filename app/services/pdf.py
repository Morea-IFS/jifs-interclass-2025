"""Lógica de geração de PDF com QR code e contexto base."""

import base64
import logging
import qrcode

from io import BytesIO

from django.http import HttpResponse
from django.template.loader import render_to_string
from reportlab.lib.utils import ImageReader
from weasyprint import HTML

logger = logging.getLogger(__name__)


def get_logo_event_type(logo_url):
    """
    Determina o tipo de logo do evento baseado nas proporções.
    0 = quadrada, 1 = retangular horizontal, 2 = retangular vertical.
    """
    img = ImageReader(logo_url)
    largura, altura = img.getSize()

    if largura == altura:
        return 0
    elif largura > altura:
        return 1
    else:
        return 2


def generate_qr_base64(data):
    """Gera um QR code e retorna como string base64."""
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()


def build_pdf_context(request, event=None):
    """
    Monta contexto base para geração de PDFs (logos, tipo de logo).
    """
    from django.utils import timezone

    cont = {
        'now': timezone.now(),
        'user': request.user,
        'logo_atum': request.build_absolute_uri('/static/images/logo_atum.png'),
    }

    if event and event.logo:
        cont['logo_ifs'] = request.build_absolute_uri(event.logo.url)
        cont['event'] = event
    else:
        cont['logo_ifs'] = request.build_absolute_uri('/static/images/logo-jiifs-2025.jpg')

    cont['logo_ifs_ofc'] = request.build_absolute_uri('/static/images/logo-ifs.svg')
    cont['logo_morea'] = request.build_absolute_uri('/static/images/logo-morea-sports.svg')
    cont['logo_event_type'] = get_logo_event_type(cont['logo_ifs'])

    return cont


def generate_pdf_response(template_name, context, filename, attachment=False):
    """Gera HttpResponse com PDF a partir de template HTML."""
    html_string = render_to_string(f'generator/{template_name}.html', context)
    response = HttpResponse(content_type='application/pdf')
    if attachment:
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    else:
        response['Content-Disposition'] = f'inline; filename="{filename}.pdf"'
    HTML(string=html_string).write_pdf(response)
    return response
