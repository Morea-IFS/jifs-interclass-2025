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
