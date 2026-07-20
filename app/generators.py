from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from unidecode import unidecode
from reportlab.pdfbase import pdfmetrics
from django.conf import settings
from reportlab.pdfbase.ttfonts import TTFont
import os, time
from django.http import HttpResponse
from .models import Certificate, Match, Occurrence, Time_pause, Event_badge, Event
from PIL import Image
from django.db.models import Min
from django.core.cache import cache
from reportlab.lib.units import mm as MM
from reportlab.lib.colors import HexColor
from django.utils import timezone  

pdfmetrics.registerFont(TTFont('MsMadi', 'fonts/MsMadi-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Outfit', 'fonts/Outfit-Black.ttf'))


def generate_certificates(players, user, t):
    w, h = (1920, 1080)

    base_certificate_path = os.path.join(settings.BASE_DIR, 'static/images/generators/base_certificate.png')
    signature_path = os.path.join(settings.BASE_DIR, 'static/images/generators/signature.png')

    base_certificate = ImageReader(base_certificate_path)
    signature = ImageReader(signature_path)

    if t == 0:
        for name in players:
            parts = name.player.name.split()
            namecertificate = parts[0].upper() + ("_" + parts[1].upper() if len(parts) > 1 else '')

            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=(w, h))
            c.drawImage(base_certificate, 0, 0, w, h)
            c.setFont("MsMadi", 100)
            c.drawCentredString(w / 2, h / 2 + 22, name.player.name)
            c.setFont("Outfit", 64)
            c.drawCentredString(540, 260, name.player.get_campus_display().upper())
            c.drawImage(signature, 1330, 60, 500, 350, mask='auto')
            c.save()

            buffer.seek(0)
            arquivo_saida = f"CERTIFICADO_{unidecode(namecertificate)}_{name.player.id}.pdf"
            certificate = Certificate.objects.create(user=user)
            certificate.name = unidecode(namecertificate)
            certificate.file.save(arquivo_saida, ContentFile(buffer.read()))
            certificate.save()
            buffer.close()
    else:
        for name in players:
            parts = name.name.split()
            namecertificate = parts[0].upper() + ("_" + parts[1].upper() if len(parts) > 1 else '')

            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=(w, h))
            c.drawImage(base_certificate, 0, 0, w, h)
            c.setFont("MsMadi", 100)
            c.drawCentredString(w / 2, h / 2 + 22, name.name)
            c.setFont("Outfit", 64)
            c.drawCentredString(540, 260, name.get_campus_display().upper())
            c.drawImage(signature, 1330, 60, 500, 350, mask='auto')
            c.save()

            buffer.seek(0)
            namebadge = f'CAMPUS_{name.get_campus_display().upper()}_{name.get_type_voluntary_display().upper()}'
            arquivo_saida = f"CRACHA_{unidecode(namebadge)}_{name.id}.pdf"
            certificate = Certificate.objects.create(user=user)
            certificate.name = unidecode(namecertificate)
            certificate.file.save(arquivo_saida, ContentFile(buffer.read()))
            certificate.save()
            buffer.close()


def draw_circular_image_optimized(c, image_reader, center_x, center_y, diameter):
    c.saveState()
    path = c.beginPath()
    path.circle(center_x, center_y, diameter / 2)
    c.clipPath(path, stroke=0, fill=0)
    c.drawImage(
        image_reader,
        center_x - diameter / 2,
        center_y - diameter / 2,
        width=diameter,
        height=diameter,
        mask='auto'
    )
    c.restoreState()


def optimize_image(path, max_size=500):
    try:
        with Image.open(path) as original:
            converted = original.convert("RGB")

            w, h = converted.size
            min_side = min(w, h)
            left, top = (w - min_side) // 2, (h - min_side) // 2
            cropped = converted.crop((left, top, left + min_side, top + min_side))
            converted.close()

            resized = cropped.resize((max_size, max_size), Image.Resampling.LANCZOS)
            cropped.close()

            buf = BytesIO()
            resized.save(buf, format="JPEG", quality=90, optimize=True)
            resized.close()

            buf.seek(0)
            return ImageReader(buf)

    except Exception as e:
        _log(f"Erro optimize_image: {e}")
        return None

def optimize_image_rect(path, target_w, target_h):
    """
    Irmã de `optimize_image()` (usada nos crachás) — MESMO padrão, mesmo
    tratamento de erro (try/except + _log, nunca deixa a geração inteira
    cair por causa de uma foto). Única diferença: em vez de sempre recortar
    quadrado, recorta na proporção retangular pedida (cover-crop), porque a
    área da foto na figurinha normalmente não é um quadrado.
    """
    try:
        with Image.open(path) as original:
            converted = original.convert("RGB")
 
            w, h = converted.size
            target_ratio = target_w / target_h
            img_ratio = w / h
 
            if img_ratio > target_ratio:
                new_h = target_h
                new_w = max(1, int(round(target_h * img_ratio)))
            else:
                new_w = target_w
                new_h = max(1, int(round(target_w / img_ratio)))
 
            resized = converted.resize((new_w, new_h), Image.Resampling.LANCZOS)
            converted.close()
 
            left = max(0, (new_w - target_w) // 2)
            top = max(0, (new_h - target_h) // 2)
            cropped = resized.crop((left, top, left + target_w, top + target_h))
            resized.close()
 
            buf = BytesIO()
            cropped.save(buf, format="JPEG", quality=90, optimize=True)
            cropped.close()
 
            buf.seek(0)
            return ImageReader(buf)
 
    except Exception as e:
        _log(f"Erro optimize_image_rect: {e}")
        return None

def _abbreviate_name(name):
    """
    Abrevia o nome para exibição no crachá.
    - Nomes com menos de 15 caracteres: retorna em maiúsculas sem alteração.
    - Nomes maiores: primeiro nome + inicial do segundo nome + ponto.
    """
    parts = name.split()
    if len(name) < 15:
        return name.upper()
    return parts[0].upper() + (" " + parts[1][0].upper() + "." if len(parts) > 1 else "")


def _deduplicate_players(players):
    """
    Remove duplicatas de player_id de uma queryset de Player_team_sport.
    Usa annotate(Min('id')) no banco quando possível; cai para deduplicação
    em memória para listas e iteradores.

    Retorna sempre uma queryset ou lista sem player_ids repetidos.
    """
    # Queryset Django → deduplicação eficiente no banco
    if hasattr(players, 'model') and hasattr(players.model, '_meta'):
        model = players.model
        # Só deduplica se o modelo tiver player_id (Player_team_sport)
        if hasattr(model, 'player'):
            unique_ids = (
                players
                .values('player_id')
                .annotate(first_id=Min('id'))
                .values_list('first_id', flat=True)
            )
            return players.filter(id__in=unique_ids).order_by('player__name')

    # Lista / iterador (Voluntary, ou lista pré-montada) → sem deduplicação
    # pois Voluntary não tem player_id duplicado por natureza
    return players


def generate_badges(players, t, namebadge, event):
    """
    Gera PDF de crachás (4 por página, layout A4) e retorna HttpResponse.

    Parâmetros
    ----------
    players : queryset ou lista
        Player_team_sport (atletas) ou Voluntary (comissão).
        A deduplicação por player_id é feita internamente.
    t : str | None
        Tipo do crachá (badge_type). None = usa user.type_voluntary.
    namebadge : str
        Nome base do arquivo PDF gerado.
    event : int
        ID do evento.
    """
    # ── Deduplicação: garante que cada atleta apareça apenas uma vez ─────────
    players = _deduplicate_players(players)

    buffer = BytesIO()

    w, h = A4
    margin = 20
    nametag_width = (w - 3 * margin) / 2
    nametag_height = (h - 3 * margin) / 2

    row_h = nametag_height + margin
    col_w = nametag_width + margin

    positions = [
        (margin, h - row_h),
        (margin + col_w, h - row_h),
        (margin, h - 2 * row_h),
        (margin + col_w, h - 2 * row_h),
    ]

    c = canvas.Canvas(buffer, pagesize=A4)
    c.setPageCompression(1)

    try:
        event_obj = Event.objects.get(id=event)
    except Event.DoesNotExist:
        buffer.close()
        raise

    badge_cache = {}

    def get_base(badge_type):
        if badge_type in badge_cache:
            return badge_cache[badge_type]
        try:
            badge = Event_badge.objects.filter(event=event_obj, number=badge_type).first()
            path = badge.file.path if badge else os.path.join(
                settings.BASE_DIR, f'static/images/generators/base_nametag__{badge_type}.png'
            )
            img = ImageReader(path)
            badge_cache[badge_type] = img
            return img
        except Exception as e:
            _log(f"Erro ao carregar base do crachá tipo {badge_type}: {e}")
            raise

    # iterator(chunk_size) reduz uso de memória em querysets grandes
    players_iter = players.iterator(chunk_size=50) if hasattr(players, 'iterator') else iter(players)

    try:
        for j, user in enumerate(players_iter):

            if j % 4 == 0 and j > 0:
                c.showPage()

            x, y = positions[j % 4]

            badge_type = str(t) if t is not None else str(user.type_voluntary)
            base_img = get_base(badge_type)
            c.drawImage(base_img, x, y, width=nametag_width, height=nametag_height)

            # ── Dados do registro ─────────────────────────────────────────────
            if hasattr(user, 'player'):
                # Player_team_sport
                obj = user.player
                photo = obj.photo
                name = obj.name
                registration = obj.registration
                description = f"TIME: {user.team_sport.team.name}"
            else:
                # Voluntary
                photo = user.photo
                name = user.name
                registration = user.registration
                description = user.unit.name.upper() if user.unit else "SEM UNIDADE"

            # ── Foto circular ─────────────────────────────────────────────────
            if photo:
                try:
                    photo_path = getattr(photo, "path", None)
                    if photo_path:
                        img = optimize_image(photo_path)
                        if img:
                            d = nametag_width / 2 + 20
                            draw_circular_image_optimized(
                                c, img,
                                x + nametag_width / 2,
                                y + nametag_height - d + 43,
                                d
                            )
                            del img
                except Exception as e:
                    _log(f"Erro ao gerar foto de {name}: {e}")

            # ── Textos ────────────────────────────────────────────────────────
            short_name = _abbreviate_name(name)

            c.setFont("Helvetica-Bold", 24)
            c.drawCentredString(x + nametag_width / 2, y + nametag_height / 2 - 30, short_name)

            c.setFont("Helvetica", 16)
            c.drawCentredString(x + nametag_width / 2, y + nametag_height / 2 - 50, str(registration))

            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(x + nametag_width / 2, y + nametag_height / 2 - 70, description)

        c.save()
        pdf_bytes = buffer.getvalue()

    except Exception:
        buffer.close()
        raise
    finally:
        if not buffer.closed:
            buffer.close()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="CRACHA_{namebadge}.pdf"'
    return response


def generate_events(name, details):
    match = Match.objects.get(status=1)
    Occurrence.objects.create(name=name, details=details, match=match)


def generate_timer(match):
    rel = time.localtime()
    seconds = 0

    if match.time_start and match.time_end:
        seconds = (
            (match.time_end.hour * 3600 + match.time_end.minute * 60 + match.time_end.second) -
            (match.time_start.hour * 3600 + match.time_start.minute * 60 + match.time_start.second)
        )
        status = 3
        pausas_totais = Time_pause.objects.filter(match=match)
        if pausas_totais.exists():
            somatorio = sum(
                (i.end_pause.hour * 3600 + i.end_pause.minute * 60 + i.end_pause.second) -
                (i.start_pause.hour * 3600 + i.start_pause.minute * 60 + i.start_pause.second)
                for i in pausas_totais
            )
            seconds -= somatorio

    elif match.time_start:
        now_seconds = rel.tm_hour * 3600 + rel.tm_min * 60 + rel.tm_sec
        start_seconds = match.time_start.hour * 3600 + match.time_start.minute * 60 + match.time_start.second
        pausas_totais = Time_pause.objects.filter(match=match)

        if pausas_totais.exists():
            pause = pausas_totais.last()

            if pause.start_pause and pause.end_pause:
                status = 1
                seconds = now_seconds - start_seconds
                somatorio = sum(
                    (i.end_pause.hour * 3600 + i.end_pause.minute * 60 + i.end_pause.second) -
                    (i.start_pause.hour * 3600 + i.start_pause.minute * 60 + i.start_pause.second)
                    for i in pausas_totais
                )
                seconds -= somatorio

            elif pause.start_pause and not pause.end_pause and pausas_totais.count() > 1:
                status = 2
                pause_start_seconds = pause.start_pause.hour * 3600 + pause.start_pause.minute * 60 + pause.start_pause.second
                seconds = pause_start_seconds - start_seconds
                somatorio = sum(
                    (i.end_pause.hour * 3600 + i.end_pause.minute * 60 + i.end_pause.second) -
                    (i.start_pause.hour * 3600 + i.start_pause.minute * 60 + i.start_pause.second)
                    for i in pausas_totais.exclude(pk=pause.pk)
                )
                seconds -= somatorio

            elif pause.start_pause and not pause.end_pause:
                status = 2
                pause_start_seconds = pause.start_pause.hour * 3600 + pause.start_pause.minute * 60 + pause.start_pause.second
                seconds = pause_start_seconds - start_seconds

        else:
            status = 1
            seconds = now_seconds - start_seconds

    else:
        seconds = 0
        status = 3

    return seconds, status


def _log(message):
    """Substitui os prinet() originais. Loga sempre, não só em DEBUG."""
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(message)
 
 
def _draw_rounded_clip(c, x, y, width, height, radius):
    """
    Clip com bordas arredondadas — o raio é limitado a, no máximo, metade
    do menor lado da caixa. Um raio maior que isso gera um path degenerado
    no reportlab (a imagem é desenhada, mas o clip corta ela inteira, sem
    erro nenhum) — por isso o limite continua aqui, é uma correção real
    e independente de como a foto é carregada.
    """
    safe_radius = max(0, min(radius, width / 2, height / 2))
    c.saveState()
    path = c.beginPath()
    path.roundRect(x, y, width, height, safe_radius)
    c.clipPath(path, stroke=0, fill=0)
 
def _draw_side_text(c, text, side, x_left_pt, x_right_pt, y_center_pt, color, font_size):
    """
    Desenha texto vertical numa lateral da figurinha.
    'left'  -> lê de baixo pra cima (rotação +90°)
    'right' -> lê de cima pra baixo (rotação -90°)
    """
    if not text:
        return
    c.saveState()
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", font_size)
    if side == 'left':
        c.translate(x_left_pt, y_center_pt)
        c.rotate(90)
    else:
        c.translate(x_right_pt, y_center_pt)
        c.rotate(-90)
    c.drawCentredString(0, 0, text.upper())
    c.restoreState()

def generate_stickers(players, template, namebadge, event_id):
    """
    Gera um PDF de figurinhas (várias por folha A4, prontas para impressão
    e recorte), com base num `Sticker_template` configurável.
 
    Reaproveita diretamente do módulo de crachás:
      - `_deduplicate_players` (mesma dedup por player_id)
      - o padrão de cache local `*_cache = {}` para a imagem base
      - `players.iterator(chunk_size=50)` para baixo consumo de memória
      - o mesmo modelo de resposta HttpResponse com Content-Disposition
 
    Parâmetros
    ----------
    players    : queryset/lista de Player_team_sport (atletas) ou Voluntary
    template   : instância de Sticker_template (geometria + arquivo base)
    namebadge  : nome base do arquivo PDF gerado
    event_id   : id do evento (usado apenas para contexto/erros)
    """
    players = _deduplicate_players(players)
 
    buffer = BytesIO()
 
    sticker_w = template.width_mm * MM
    sticker_h = template.height_mm * MM
    page_w, page_h = A4
    margin, gap = 8, 6

    cols = max(1, int((page_w - 2 * margin + gap) // (sticker_w + gap)))
    rows = max(1, int((page_h - 2 * margin + gap) // (sticker_h + gap)))
    per_page = cols * rows

    photo_w_pt = sticker_w * (template.photo_width / 100.0)
    photo_h_pt = sticker_h * (template.photo_height / 100.0)
    photo_x_pt = sticker_w * (template.photo_x / 100.0)
    photo_y_pt = sticker_h * (1 - (template.photo_y / 100.0)) - photo_h_pt
    radius_pt = photo_w_pt * (template.photo_corner_radius / 100.0)

    name_y_pt = sticker_h * (1 - (template.name_y / 100.0))

    photo_px_w = max(200, int(photo_w_pt * 3))
    photo_px_h = max(200, int(photo_h_pt * 3))

    try:
        base_image = ImageReader(template.base_image.path)
    except Exception as e:
        buffer.close()
        raise ValueError(f"Não foi possível carregar a imagem do template de figurinha: {e}")

    name_color = HexColor(template.name_color or "#FFFFFF")
    side_color = HexColor(getattr(template, 'side_color', '#FFFFFF') or '#FFFFFF')
    side_font = getattr(template, 'side_font_size', 22)

    # ano: usa o ano de início do evento (fallback: ano atual)
    try:
        event_obj = Event.objects.get(id=event_id)
        year_text = str(event_obj.date_init.year) if event_obj.date_init else str(timezone.now().year)
    except Event.DoesNotExist:
        year_text = str(timezone.now().year)

    c = canvas.Canvas(buffer, pagesize=A4)
    c.setPageCompression(1)
    players_iter = players.iterator(chunk_size=50) if hasattr(players, 'iterator') else iter(players)

    try:
        for j, item in enumerate(players_iter):
            if j % per_page == 0 and j > 0:
                c.showPage()
            slot = j % per_page
            col, row = slot % cols, slot // cols
            x = margin + col * (sticker_w + gap)
            y = page_h - margin - (row + 1) * sticker_h - row * gap

            if hasattr(item, 'player'):
                obj = item.player
                photo = obj.photo
                display_name = (obj.name or '').strip()
                team_name = item.team_sport.team.name if item.team_sport and item.team_sport.team else ''
                campus_name = obj.unit.name if obj.unit else ''
            else:
                obj = item
                photo = obj.photo
                display_name = (obj.name or '').strip()
                team_name = ''
                campus_name = obj.unit.name if obj.unit else ''

            c.drawImage(base_image, x, y, width=sticker_w, height=sticker_h)

            if photo:
                try:
                    photo_path = getattr(photo, "path", None)
                    if photo_path:
                        img = optimize_image_rect(photo_path, photo_px_w, photo_px_h)
                        if img:
                            _draw_rounded_clip(
                                c,
                                x + photo_x_pt, y + photo_y_pt,
                                photo_w_pt, photo_h_pt,
                                radius_pt,
                            )
                            c.drawImage(
                                img,
                                x + photo_x_pt, y + photo_y_pt,
                                width=photo_w_pt, height=photo_h_pt,
                                mask='auto',
                            )
                            c.restoreState()
                            del img
                except Exception as e:
                    _log(f"Erro ao gerar foto da figurinha de {display_name}: {e}")

            # nome — MESMA abreviação usada nos crachás, pra nunca estourar o layout
            if template.show_name and display_name:
                short_name = _abbreviate_name(display_name)
                c.setFillColor(name_color)
                c.setFont("Helvetica-Bold", template.name_font_size)
                c.drawCentredString(x + sticker_w / 2, y + name_y_pt, short_name.upper())
                c.setFillColorRGB(0, 0, 0)

            x_left_pt = x + sticker_w * 0.08
            x_right_pt = x + sticker_w * 0.92
            y_center_pt = y + sticker_h * 0.5

            if getattr(template, 'show_campus', False) and campus_name:
                _draw_side_text(
                    c, campus_name, getattr(template, 'campus_side', 'left'),
                    x_left_pt, x_right_pt, y_center_pt, side_color, side_font
                )

            if getattr(template, 'show_year', False) and year_text:
                _draw_side_text(
                    c, year_text, getattr(template, 'year_side', 'right'),
                    x_left_pt, x_right_pt, y_center_pt, side_color, side_font
                )

        c.save()
        pdf_bytes = buffer.getvalue()
    except Exception:
        buffer.close()
        raise
    finally:
        if not buffer.closed:
            buffer.close()

    safe_name = namebadge.replace(' ', '_').replace('/', '_')
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="FIGURINHA_{safe_name}.pdf"'
    return response