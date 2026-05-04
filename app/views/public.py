"""
Views extraídas automaticamente do views.py monolítico.
Módulo: public.py
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

def events_list(request):
    if request.method == 'GET':
        events = Event.objects.all().order_by('-id')
        if len(events) == 1:
            return redirect('home_public', events[0].id)
        return render(request, 'public/events_list.html', {'events': events})
    else:
        return redirect('events')

def home_public(request, event_id):
        event = Event.objects.get(id=event_id)
        hoje = timezone.localdate()
        games_day = Match.objects.filter(time_match__date=hoje, event=event).prefetch_related('teams__team').order_by('time_match')
        context_games_day = [
            {
                'match': match,
                'times': list(match.teams.all()),
            }
            for match in games_day
        ]


        volei_masc = Volley_match.objects.filter(matches__sexo=0, event=event).prefetch_related('matches__teams__team').distinct()
        context_volei_masc = [
            {
                'volley_match': volley_match,
                'sets_team_a': volley_match.sets_team_a,
                'sets_team_b': volley_match.sets_team_b,
                'matches': [
                    {
                        'match': match,
                        'times': [
                            {
                                'team': team_match.team,
                                'name': team_match.team.name,
                                'photo_url': team_match.team.photo.url,
                                'points': Point.objects.filter(team_match=team_match).count()
                            }
                            for team_match in match.teams.all()
                        ]
                    }
                    for match in volley_match.matches.all().order_by('time_match')
                ]
            }
            for volley_match in volei_masc
        ]

        volei_fem = Volley_match.objects.filter(matches__sexo=1, event=event).prefetch_related('matches__teams__team').distinct()
        context_volei_fem = [
            {
                'volley_match': volley_match,
                'sets_team_a': volley_match.sets_team_a,
                'sets_team_b': volley_match.sets_team_b,
                'matches': [
                    {
                        'match': match,
                        'times': [
                            {
                                'team': team_match.team,
                                'name': team_match.team.name,
                                'photo_url': team_match.team.photo.url,
                                'points': Point.objects.filter(team_match=team_match).count()
                            }
                            for team_match in match.teams.all()
                        ]
                    }
                    for match in volley_match.matches.all().order_by('time_match')
                ]
            }
            for volley_match in volei_fem
        ]
        
        matchs_futsal_masc = Match.objects.filter(sport=0, sexo=0, event=event).prefetch_related('teams__team').order_by('time_match')
        context_futsal_masc = [
            {
                'match': match,
                'times': list(match.teams.all()),
                'points_a': Point.objects.filter(team_match=match.teams.first()).count(),
                'points_b': Point.objects.filter(team_match=match.teams.last()).count(),
            }
            for match in matchs_futsal_masc
        ]

        matchs_futsal_fem = Match.objects.filter(sport=0, sexo=1, event=event).prefetch_related('teams__team').order_by('time_match')
        context_futsal_fem = [
            {
                'match': match,
                'times': list(match.teams.all()),
                'points_a': Point.objects.filter(team_match=match.teams.first()).count(),
                'points_b': Point.objects.filter(team_match=match.teams.last()).count(),
            }
            for match in matchs_futsal_fem

        ]

        matchs_handebol_masc = Match.objects.filter(sport=3, sexo=0, event=event).prefetch_related('teams__team').order_by('time_match')
        context_handebol_masc = [
            {
                'match': match,
                'times': list(match.teams.all()),
                'points_a': Point.objects.filter(team_match=match.teams.first()).count(),
                'points_b': Point.objects.filter(team_match=match.teams.last()).count(),
            }
            for match in matchs_handebol_masc
        ]

        matchs_handebol_fem = Match.objects.filter(sport=3, sexo=1, event=event).prefetch_related('teams__team').order_by('time_match')
        context_handebol_fem = [
            {
                'match': match,
                'times': list(match.teams.all()),
                'points_a': Point.objects.filter(team_match=match.teams.first()).count(),
                'points_b': Point.objects.filter(team_match=match.teams.last()).count(),
            }
            for match in matchs_handebol_fem

        ]

        matchs_queimado_fem = Match.objects.filter(sport=8, sexo=0, event=event).prefetch_related('teams__team').order_by('time_match')
        context_queimado_fem = [
            {
                'match': match,
                'times': list(match.teams.all()),
                'points_a': Point.objects.filter(team_match=match.teams.first()).count(),
                'points_b': Point.objects.filter(team_match=match.teams.last()).count(),
            }
            for match in matchs_queimado_fem
        ]

        matchs_queimado_masc = Match.objects.filter(sport=8, sexo=1, event=event).prefetch_related('teams__team').order_by('time_match')
        context_queimado_masc = [
            {
                'match': match,
                'times': list(match.teams.all()),
                'points_a': Point.objects.filter(team_match=match.teams.first()).count(),
                'points_b': Point.objects.filter(team_match=match.teams.last()).count(),
            }
            for match in matchs_queimado_masc
        ]
        event_sports = Event_sport.objects.filter(event=event)
        attachments = Attachments.objects.filter(public=True, event=event)

        if request.method == "GET":
            context = {
                'context_queimado_masc':context_queimado_masc,
                'context_queimado_fem':context_queimado_fem,
                'context_volei_masc':context_volei_masc,
                'context_volei_fem':context_volei_fem,
                'context_futsal_masc':context_futsal_masc,
                'context_futsal_fem':context_futsal_fem,
                'context_handebol_masc':context_handebol_masc,
                'context_handebol_fem':context_handebol_fem,
                'context_games_day':context_games_day,
                'event':event,
                'event_sports':event_sports,
                'attachments':attachments,
                'Phase_types': Phase_types,
            }
            
            return render(request, 'public/home_public.html', context)

@login_required(login_url="login")
@terms_accept_required
def home_admin(request):
    user = request.user
    if user.type != 0:
        event = Event.objects.get(id=user.event_user.id)
        help = Help.objects.all()
        ins = Settings_access.objects.all().last()
        vistos = Statement_user.objects.filter(user=user).values_list('statement_id', flat=True)

        statements_faltando = Statement.objects.exclude(id__in=vistos)

        if statements_faltando.exists():
            imagem_filter = statements_faltando.first()
            imagem = Statement.objects.get(id=imagem_filter.id)
            Statement_user.objects.create(user=user, statement=imagem)
        else:
            imagem = None
    
        return render(request, 'home_admin.html',{'help':help,'ins':ins,'mensagem':'mensagem','imagem':imagem,'event':event})
    else:
        event = Event.objects.all().order_by('active')
        context = {
            'event':event,
            'total_events': Event.objects.all().count(),
            'total_teams': Team_sport.objects.all().count(),
            'total_players': Player.objects.all().count(),
            'total_users': User.objects.all().count(),
        }
        return render(request, 'home_admin_adm.html', context)

def switching_public(request, event_id):
        event = Event.objects.get(id=event_id)
        event_sports = Event_sport.objects.filter(event=event)

        if request.method == "GET":
            context = {
                'event':event,
                'event_sports':event_sports,
                'phase_types': Phase_types.choices,
                'sexo_types': Sexo_types.choices,
                'phases_all': Phase.objects.filter(event__event=event).order_by('event'),
            }
            phases = Phase.objects.filter(event__event=event)\
                .prefetch_related(
                    'groups__group_matches__teams__team', 
                )
            if request.GET.get('sport') and request.GET.get('sport') != '':
                event_sport = get_object_or_404(Event_sport, id=request.GET.get('sport'))
                phases = phases.filter(event=event_sport)
                context['event_sport'] = event_sport

            if request.GET.get('genre') and request.GET.get('genre') != '':
                phases = phases.filter(sexo=int(request.GET.get('genre')))
                context['genre'] = int(request.GET.get('genre'))

            if request.GET.get('phase') and request.GET.get('phase') != '':
                phases = phases.filter(name=int(request.GET.get('phase')))
                context['phase'] = int(request.GET.get('phase'))

            matches_by_phase = {}

            for phase in phases:
                matches_no_group = Match.objects.filter(
                    event=event,
                    group_phase__isnull=True,
                )

                matches_in_groups = Match.objects.filter(
                    event=event,
                    group_phase__phase=phase,
                )

                matches_by_phase[phase.id] = matches_no_group | matches_in_groups
                matches_by_phase[phase.id] = matches_by_phase[phase.id].prefetch_related('teams__team')

            
            context['phases'] = phases
            context['matches_by_phase'] = matches_by_phase
            
            return render(request, 'public/switching.html', context)
        else:
            return redirect('switching')

def about_us(request, event_id):
    event = Event.objects.get(id=event_id)
    return render(request, 'public/about_us.html',{'event':event})

def authenticate_file(request):
    context = {}
    if 'code' in request.GET and request.GET.get('code') != '':
        code = str(request.GET.get('code'))
        if Authenticity.objects.filter(code=code):
            context['authenticity'] = Authenticity.objects.filter(code=code)[0]
        context['status'] = True
        
    return render(request, 'public/authenticate.html', context)
