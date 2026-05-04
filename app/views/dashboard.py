"""
Views extraídas automaticamente do views.py monolítico.
Módulo: dashboard.py
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, QueryDict
from app.models import Sexo_types, Settings_access, UserSession, Event_unit, Event_badge, Detailed, Status, Authenticity, Match_referee, Type_referee, Replacement, Group_phase, Phase, Phase_types, Campus_types, Help, Type_penalties, Detailed, Activity, Statement, Point_types, Event, Event_sport, Statement_user, Users_types, Type_service, Certificate, Attachments, Volley_match, Player, Sport_types, Voluntary, Penalties, Occurrence, Time_pause, Team, Point, Team_sport, Player_team_sport, Match, Team_match, Player_match, Assistance,  Banner, Terms_Use
from django.db.models import Count, Q, Prefetch
from app.decorators import time_restriction
from django.contrib import messages
from django.db import IntegrityError
from django.templatetags.static import static
from django.contrib.auth.models import User, Group, Permission
from django.contrib.sessions.models import Session
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login as auth_login, authenticate, logout, get_user_model
from django.template.loader import render_to_string
from app.forms import Terms_UseForm
from datetime import date, datetime
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from app.generators import generate_certificates, generate_badges, generate_events, generate_timer
import time, pytz, os, random
from django.core.files.base import ContentFile
from weasyprint import HTML
from django.utils import timezone
from app.decorators import terms_accept_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import PermissionDenied
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import io
import pytz
from datetime import datetime as dt
from collections import Counter
from django.db.models.functions import TruncDate
from django.db.models import Count
from datetime import date, timedelta
from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from app.models import AccessLog, UserSession
from app.decorators import terms_accept_required
from datetime import date, timedelta
from app.models import AccessLog, Event

# Imports locais do projeto
from app.helpers import (
    acesso_evento, acesso_team, acesso_team_sport,
    acesso_player, acesso_match, verificar_foto,
    type_file, calcular_idade, generate_authenticity,
    check_gender_compatibility, player_queryset_for_team,
    SEXO_NAMES,
)
from app.services.pdf import build_pdf_context, generate_pdf_response, generate_qr_base64
from app.services.points import calculate_points, calculate_penalties_count, get_aces_count
from app.services.volleyball import get_ordered_team_matches, get_ordered_sets
from app.services.password import generate_random_password

@login_required(login_url="login")
@terms_accept_required
def dashboard_acesso(request):
    user = request.user

    if not user.is_superuser and getattr(user, "type", None) not in [0, 1]:
        messages.error(request, "Você não tem permissão para acessar essa página.")
        return redirect("Home")

    user_model = get_user_model()

    selected_event_id = request.GET.get("e", "").strip()
    selected_user_id = request.GET.get("u", "").strip()
    selected_date_raw = request.GET.get("d", "").strip()

    try:
        selected_date_obj = date.fromisoformat(selected_date_raw) if selected_date_raw else None
    except ValueError:
        selected_date_obj = None
        selected_date_raw = ""

    events = None
    event = None

    if user.type == 0:
        events = Event.objects.all().order_by("name")

        if selected_event_id:
            try:
                event = Event.objects.get(id=selected_event_id)
            except Event.DoesNotExist:
                messages.error(request, "Evento selecionado não foi encontrado.")
                selected_event_id = ""
                event = None

    elif user.type == 1:
        event = user.event_user
        if not event:
            messages.error(request, "Seu usuário não possui evento vinculado.")
            return redirect("Home")
        selected_event_id = str(event.id)

    if user.type == 0 and not event:
        context = {
            "events": events,
            "event": None,
            "select_event": selected_event_id,
            "all_users": [],
            "selected_user_id": "",
            "selected_user_obj": None,
            "selected_date": selected_date_raw,
            "total_users": 0,
            "total_accepted": 0,
            "total_docs": 0,
            "total_pendentes": 0,
            "acessos_hoje": 0,
            "acessos_7dias": [],
            "user_rows": [],
        }
        return render(request, "dashboard_acesso.html", context)

    all_users = (
        user_model.objects
        .exclude(is_superuser=True)
        .filter(event_user=event)
        .order_by("username")
    )

    selected_user_obj = None
    users_qs = all_users

    if selected_user_id:
        users_qs = all_users.filter(id=selected_user_id)
        selected_user_obj = users_qs.first()

    hoje = timezone.localdate()

    total_users = all_users.count()
    total_accepted = all_users.filter(accepted=True).count()
    total_docs = sum(1 for u in all_users if _has_user_document(u))
    total_pendentes = sum(
        1
        for u in all_users
        if (not getattr(u, "accepted", False)) or (not _has_user_document(u))
    )

    acessos_hoje = (
        AccessLog.objects.filter(
            event=event,
            accessed_at__date=hoje
        )
        .values("user")
        .distinct()
        .count()
    )

    acessos_7dias_raw = []
    max_count = 0

    for i in range(6, -1, -1):
        dia = hoje - timedelta(days=i)
        count = (
            AccessLog.objects.filter(
                event=event,
                accessed_at__date=dia
            )
            .values("user")
            .distinct()
            .count()
        )
        acessos_7dias_raw.append({"dia": dia, "count": count})
        max_count = max(max_count, count)

    acessos_7dias = []
    for item in acessos_7dias_raw:
        count = item["count"]
        pct = max(6, round((count / max_count) * 100)) if max_count > 0 else 0

        acessos_7dias.append(
            {
                "label": item["dia"].strftime("%d/%m"),
                "count": count,
                "pct": pct,
            }
        )

    user_rows = []
    for u in users_qs:
        row = _build_user_dashboard_row(
            u,
            selected_date=selected_date_obj,
            event=event,
        )
        user_rows.append(row)

    context = {
        "events": events,
        "event": event,
        "select_event": selected_event_id,
        "all_users": all_users,
        "selected_user_id": selected_user_id,
        "selected_user_obj": selected_user_obj,
        "selected_date": selected_date_raw,
        "total_users": total_users,
        "total_accepted": total_accepted,
        "total_docs": total_docs,
        "total_pendentes": total_pendentes,
        "acessos_hoje": acessos_hoje,
        "acessos_7dias": acessos_7dias,
        "user_rows": user_rows,
    }
    return render(request, "dashboard_acesso.html", context)

@login_required(login_url="login")
@terms_accept_required
def dashboard_acesso_user_detail(request, user_id):
    user = request.user

    if not user.is_superuser and getattr(user, "type", None) not in [0, 1]:
        return JsonResponse({"error": "Sem permissão"}, status=403)

    selected_event_id = request.GET.get("e", "").strip()

    event = None
    if user.type == 0:
        if selected_event_id:
            event = Event.objects.filter(id=selected_event_id).first()
    elif user.type == 1:
        event = user.event_user

    if not event:
        return JsonResponse({"error": "Evento não selecionado"}, status=400)

    user_model = get_user_model()
    u = user_model.objects.filter(
        id=user_id,
        event_user=event
    ).first()

    if not u:
        return JsonResponse({"error": "Não encontrado"}, status=404)

    row_data = _build_user_dashboard_row(u, event=event)

    access_logs_qs = (
        AccessLog.objects.filter(user=u, event=event)
        .select_related("session", "event")
        .order_by("-accessed_at")[:10]
    )

    service_map = {
        "team_manage": "Times",
        "player_manage": "Atletas",
        "voluntary_manage": "Equipe",
        "games": "Partidas",
        "badge": "Crachás",
        "data": "Relatórios",
        "spreadsheet": "Planilhas",
        "certificate": "Certificados",
        "attachments": "Anexos",
        "scoreboard": "Placar",
        "user_manage": "Usuários",
        "Home": "Início",
        "event_manage": "Eventos",
    }

    sessions_data = []

    for log in access_logs_qs:
        session_data = {}
        services = []

        try:
            if log.session:
                session_data = log.session.get_decoded() or {}
                visited = session_data.get("visited_urls", []) or []
                services = list(
                    dict.fromkeys(
                        [service_map.get(url, url) for url in visited if url]
                    )
                )
        except Exception:
            session_data = {}
            services = []

        sessions_data.append(
            {
                "date": _format_dt(log.accessed_at),
                "services": services,
                "ip": log.ip_address or session_data.get("client_ip", ""),
            }
        )

    full_name = (
        getattr(u, "get_full_name", lambda: "")().strip()
        or getattr(u, "first_name", "")
        or u.username
    )

    data = {
        "username": u.username,
        "full_name": full_name,
        "first_name": u.first_name or "",
        "email": u.email or "",
        "telefone": getattr(u, "telefone", "") or "",
        "type_display": u.get_type_display() if hasattr(u, "get_type_display") else "",
        "photo": u.photo.url if getattr(u, "photo", None) else "",
        "event_user": u.event_user.name if getattr(u, "event_user", None) else "",
        "unit": u.unit.name if getattr(u, "unit", None) else "",
        "team": u.team.name if getattr(u, "team", None) else "",
        "accepted": row_data["accepted"],
        "accepted_at": _format_dt(row_data["accepted_at"]),
        "has_document": row_data["has_document"],
        "document_url": u.document.url if _has_user_document(u) else "",
        "primeiro_login": _format_dt(row_data["primeiro_login"]),
        "ultimo_login": _format_dt(row_data["ultimo_login"]),
        "total_acessos": row_data["total_acessos"],
        "sessions": sessions_data,
    }

    return JsonResponse(data)

def _has_user_document(user):
    doc = getattr(user, "document", None)
    return bool(doc and str(doc).strip())

def _format_dt(dt):
    if not dt:
        return ""
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return dt.strftime("%d/%m/%Y %H:%M")

def _get_user_access_qs(user, selected_date=None, event=None):
    qs = AccessLog.objects.filter(user=user)

    if event:
        qs = qs.filter(event=event)

    if selected_date:
        qs = qs.filter(accessed_at__date=selected_date)

    return qs.order_by("accessed_at")

def _build_user_dashboard_row(user, selected_date=None, event=None):
    access_qs = _get_user_access_qs(user, selected_date=selected_date, event=event)

    total_acessos = access_qs.count()
    primeiro_acesso = access_qs.first()
    ultimo_acesso = access_qs.order_by("-accessed_at").first()

    return {
        "user": user,
        "primeiro_login": primeiro_acesso.accessed_at if primeiro_acesso else None,
        "ultimo_login": ultimo_acesso.accessed_at if ultimo_acesso else None,
        "total_acessos": total_acessos,
        "accepted": bool(getattr(user, "accepted", False)),
        "accepted_at": getattr(user, "accepted_at", None),
        "has_document": _has_user_document(user),
    }
