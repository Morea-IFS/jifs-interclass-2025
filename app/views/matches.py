"""
Views extraídas automaticamente do views.py monolítico.
Módulo: matches.py
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
@permission_required('app.view_match', raise_exception=True)
def matches_manage(request):
    try:
        matchs = Match.objects.all().prefetch_related('teams__team')
        sport = Sport_types.choices
        context = [
            {
                'match': match,
                'sport':sport,
                'times': list(match.teams.all()),
                
            }
            for match in matchs
        ]
        if request.method == "GET":
            if not context:
            return render(request, 'matches/matches_manage.html',{'context': context})
        else:
            match_id = request.POST.get('match_delete')
            match_delete = Match.objects.get(id=match_id)
            if match_delete.sport == 1:
                if Volley_match.objects.filter(id=match_delete.volley_match.id):
                    volley_match = Volley_match.objects.get(id=match_delete.volley_match.id)
                    matches = Match.objects.filter(volley_match=volley_match.id)
                    if len(matches) < 2:
                        volley_match.delete()
            match_delete.delete()
            return redirect('matches_manage')
    except Exception as e:
        messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return redirect('matches_manage')

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.change_match', raise_exception=True)
def matches_edit(request, id):
    try:
        match = get_object_or_404(Match, id=id)
        team_matchs = Team_match.objects.filter(match=match)
        team = Team.objects.all()
        team_match_a = team_matchs[0]
        team_match_b = team_matchs[1]
        match = get_object_or_404(Match, id=id)
        sport = Sport_types.choices
        if match.sexo != 1 or 0:
            match_disable = True
        else:
            match_disable = False
        
        context = {
            'match': match, 
            'sport': sport,
            'team': team,
            'team_match_a': team_match_a,
            'team_match_b': team_match_b,
            'match_disable': match_disable,
        }
        if request.method == "GET":
            return render(request, 'matches/matches_edit.html', context)
        else:
            if 'excluir' in request.POST:
                match.delete()
                if match.sport == 1:
                    volley_match = Volley_match.objects.get(id=match.volley_match.id)
                    volley_match.delete()
                team_match_a.delete()
                team_match_b.delete()
                return redirect('matches_manage')
            else:
                sport_select = int(request.POST.get('sport'))
                match.sport = sport_select
                match.sport = sport
                match.sexo = request.POST.get('sexo')
                match.time_match = request.POST.get('datatime')
                team_a = request.POST.get('team_a')
                team_b = request.POST.get('team_b')
                team_match_a.team = get_object_or_404(Team, id=team_a)
                team_match_b.team = get_object_or_404(Team, id=team_b)
                team_match_a.save()
                team_match_b.save()
                match.time_match = request.POST.get('datetime')
                match.save()
    except (TypeError, ValueError):
        messages.error(request, 'Um valor foi informado incorretamente!')
    except IntegrityError as e:
        messages.error(request, 'Algumas informações não foram preenchidas :(')
    except Team.DoesNotExist:
        messages.error(request, 'Um dos times não foi informado ou é inexistente!')
    except Exception as e:
        messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
    return redirect('matches_manage')

@login_required(login_url="login")
@terms_accept_required
def games(request):
    if request.method == "GET":
        context = {
            'team': Team.objects.all(),
            'sport': Sport_types.choices,
            'events': Event.objects.all(),
            'phase_types': Phase_types.choices,
            'sexo': Sexo_types.choices,
        }

        selected_event = None

        if 'e' in request.GET and request.GET['e'] != '':
            selected_event = Event.objects.get(id=request.GET['e'])
            context['select_event'] = request.GET['e']
            context['phases'] = Phase.objects.filter(event__event__id=request.GET['e']).order_by('name','event','sexo')
            context['groups'] = Group_phase.objects.filter(phase__event__event__id=request.GET['e']).order_by('phase__name','phase__event','phase__sexo')
            context['event_sports'] = Event_sport.objects.filter(event=selected_event)
            context['teams'] = Team.objects.filter(event=selected_event)
        elif request.user.event_user:
            selected_event = request.user.event_user
            context['event_sports'] = Event_sport.objects.filter(event=request.user.event_user)
            context['phases'] = Phase.objects.filter(event__event=request.user.event_user).order_by('name','event','sexo')
            context['groups'] = Group_phase.objects.filter(phase__event__event=request.user.event_user).order_by('phase__name','phase__event','phase__sexo')

        if selected_event:
            matches = Match.objects.filter(event__id=selected_event.id).prefetch_related('teams__team').order_by('time_match')
        else:
            context['phases'] = []
            context['groups'] = []
            matches = Match.objects.all().prefetch_related('teams__team').order_by('time_match')

        context['context'] = [
            {
                'match': match,
                'times': list(match.teams.all()),
                'points_a': Point.objects.filter(team_match=match.teams.first()).count(),
                'points_b': Point.objects.filter(team_match=match.teams.last()).count(),
            }
            for match in matches
        ]

        return render(request, 'games.html', context)

    elif 'change_match' in request.POST:
        match = Match.objects.get(id=request.POST.get('change_match'))

        if Match.objects.filter(status=1, event=match.event).exists():
            messages.info(request, "Já existe uma partida em andamento. Finalize-a antes de iniciar outra.")
        elif match.status == 0:
            if match.volley_match:
                volley_match = Volley_match.objects.get(id=match.volley_match.id)
                volley_match.status = 1
                volley_match.save()
            match.status = 1
            match.save()
            return redirect('scoreboard', match.event.id)
        else:
            messages.info(request, "A partida já foi finalizada.")
        return redirect('games')

    # 2️⃣ Criar nova FASE
    elif 'create_phase' in request.POST:
        if not request.user.has_perm('app.add_phase'):
            messages.error(request, "Você não tem permissão para criar fases.")
            return redirect('games')
        event_id = int(request.POST.get('event_sport'))
        name = int(request.POST.get('name'))
        sexo = int(request.POST.get('sexo_phase'))
        if not event_id or not name or not sexo:
            if not name == 0 and not name or not sexo == 0 and not sexo:
                messages.error(request, "Dados insuficientes para criar a fase.")
                return redirect('games')

        event_sport = Event_sport.objects.get(id=event_id)
        if not event_sport:
            messages.error(request, "Evento ou esporte não encontrado.")
            return redirect('games')

        Phase.objects.create(event=event_sport, name=name, sexo=sexo)
        messages.success(request, "Fase criada com sucesso!")
        return redirect(f"{reverse('games')}?e={event_sport.event.id}")

    # 3️⃣ Criar novo GRUPO
    elif 'create_group' in request.POST:
        if not request.user.has_perm('app.add_group_phase'):
            messages.error(request, "Você não tem permissão para criar grupos.")
            return redirect('games')

        phase_id = request.POST.get('phase')
        group_name = request.POST.get('group_name')

        if not phase_id:
            messages.error(request, "Preencha todos os campos para criar o grupo.")
            return redirect('games')

        phase = Phase.objects.get(id=phase_id)
        Group_phase.objects.create(phase=phase, name=group_name)
        messages.success(request, "Grupo criado com sucesso!")
        return redirect(f"{reverse('games')}?e={phase.event.event.id}")

    elif 'time_a' in request.POST and 'time_b' in request.POST:

        # 4️⃣ Criar nova PARTIDA
        event_sport = Event_sport.objects.get(id=int(request.POST.get('sport')))
        sport_id = event_sport.sport
        sexo = request.POST.get('sexo')
        team_a_id = request.POST.get('time_a')
        team_b_id = request.POST.get('time_b')
        datetime = request.POST.get('datetime')
        group_phase_id = request.POST.get('group')
        location = request.POST.get('location')

        if group_phase_id:
            if sport_id != Group_phase.objects.get(id=group_phase_id).phase.event.sport:
                messages.error(request, "O grupo precisa corresponder ao esporte.")
                return redirect('games')

        # Define o evento
        if not request.user.event_user:
            if 'e' in request.GET and request.GET['e'] != '':
                event = Event.objects.get(id=request.GET['e'])
            else:
                messages.error(request, "Selecione um evento válido.")
                return redirect('games')
        else:
            event = request.user.event_user

        # Validações
        if team_a_id == team_b_id:
            messages.error(request, "Você não pode criar uma partida com times iguais!")
            return redirect('games')

        team_a = Team.objects.get(id=team_a_id)
        team_b = Team.objects.get(id=team_b_id)

        team_sport_a = Team_sport.objects.filter(team=team_a, sport=event_sport, sexo=sexo).first()
        team_sport_b = Team_sport.objects.filter(team=team_b, sport=event_sport, sexo=sexo).first()

        if not team_sport_a or not team_sport_b:
            messages.error(request, "Algum time não está cadastrado na modalidade selecionada!")
            return redirect('games')
        
        if sport_id in [1, 2]:
            volley_match = Volley_match.objects.create(status=0, event=event)
            volley_match.save()
            match, created = Match.objects.get_or_create(
                sport=sport_id,
                sexo=sexo,
                time_match=datetime,
                volley_match=volley_match,
                event=event,
                defaults={
                    'group_phase_id': group_phase_id or None,
                    'location': location or "",
                }
            )
        else:
            match, created = Match.objects.get_or_create(
                sport=sport_id,
                sexo=sexo,
                time_match=datetime,
                event=event,
                defaults={
                    'group_phase_id': group_phase_id or None,
                    'location': location or "",
                }
            )

        if created:
            Team_match.objects.create(match=match, team=team_a)
            Team_match.objects.create(match=match, team=team_b)
            messages.success(request, "Partida cadastrada com sucesso!")
        else:
            messages.info(request, f"Essa partida já foi cadastrada! Identificação: #{match.id}")

        team_matches = Team_match.objects.filter(match=match)
        team_match_a = team_matches[0]
        team_match_b = team_matches[1]
  
        players_match_a = Player_match.objects.filter(team_match=team_match_a)
        players_match_b = Player_match.objects.filter(team_match=team_match_b)


        player_team_sport_a = Player_team_sport.objects.filter(team_sport=team_sport_a)
        player_team_sport_b = Player_team_sport.objects.filter(team_sport=team_sport_b)

        for i in player_team_sport_a:
            Player_match.objects.get_or_create(player=i.player, match=match, team_match=team_match_a)
        for i in player_team_sport_b:
            Player_match.objects.get_or_create(player=i.player, match=match, team_match=team_match_b)

        for i in players_match_a:
            if not Player_team_sport.objects.filter(player=i.player, team_sport=team_sport_a).exists():
                i.delete()
        for i in players_match_b:
            if not Player_team_sport.objects.filter(player=i.player, team_sport=team_sport_b).exists():
                i.delete()

    elif 'sumula' in request.POST:
        match = Match.objects.get(id=request.POST.get('sumula'))
        match_referee = Match_referee.objects.filter(match=match)
        team_match = Team_match.objects.filter(match=match)
        players_match_a = Player_match.objects.filter(team_match=team_match[0])
        players_match_b = Player_match.objects.filter(team_match=team_match[1])
        team_sport_a = Team_sport.objects.get(team=team_match[0].team, sport__sport=team_match[0].match.sport, sexo=team_match[0].match.sexo)
        team_sport_b = Team_sport.objects.get(team=team_match[1].team, sport__sport=team_match[1].match.sport, sexo=team_match[1].match.sexo)
        point_a = Point.objects.filter(team_match=team_match[0])
        point_b = Point.objects.filter(team_match=team_match[1])
        replacements = Replacement.objects.filter(team_match__match=match)
        players_a = [
            {
            'name': i.player.name,
            'number': i.player_number,
            'card_r': Penalties.objects.filter(player=i.player, team_match=team_match[0], type_penalties=0).count(),
            'card_y': Penalties.objects.filter(player=i.player, team_match=team_match[0], type_penalties=1).count(),
            'point': Point.objects.filter(player=i.player, team_match=team_match[0]).count(),
            }
            for i in players_match_a
        ]
        players_b = [
            {
            'name': i.player.name,
            'number': i.player_number,
            'card_r': Penalties.objects.filter(player=i.player, team_match=team_match[0], type_penalties=0).count(),
            'card_y': Penalties.objects.filter(player=i.player, team_match=team_match[0], type_penalties=1).count(),
            'point': Point.objects.filter(player=i.player, team_match=team_match[0]).count(),
            }
            for i in players_match_b
        ]

        authenticity = generate_authenticity(f"Súmula gerada por {request.user.username} da partida entre {team_match[0].team.name} e {team_match[1].team.name}", match.event)
        link = f"https://{request.get_host()}/autenticar?code={authenticity.code}"
        qr = qrcode.make(link)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        context = {
            'match':match,
            'team_match_a':team_match[0],
            'team_match_b':team_match[1],
            'players_a':players_a,
            'players_b':players_b,
            'team_sport_a':team_sport_a,
            'team_sport_b':team_sport_b,
            'point_a':point_a,
            'point_b':point_b,
            'replacements': replacements,
            'user': request.user,
            'match_referee': match_referee,
            'authenticity': authenticity,
            'qr_code': img_base64,
            'logo_ifs': request.build_absolute_uri('/static/images/logo-ifs-black.svg'),
            'logo_morea': request.build_absolute_uri('/static/images/logo-morea.svg'),
            
        }
        html_string = render_to_string('generator/sumula.html', context)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="sumula-{authenticity.number}.pdf"'
        #response['Content-Disposition'] = f'attachment; filename="sumula.pdf"'

        HTML(string=html_string).write_pdf(response)

        return response
    return redirect('games')

@login_required(login_url="login")
@permission_required('app.view_match', raise_exception=True)
def match_settings(request, id_sport, id_match):
    match = get_object_or_404(Match, id=id_match)
    current_get_params = request.GET.urlencode()
    if not _acesso_match(request.user, match):
        messages.error(request, "Você não tem permissão para acessar esta partida.")
        return redirect('games')
    if request.method == "GET":
        match=match
        time_pauses = Time_pause.objects.filter(match=match)
        assistance = Assistance.objects.filter(assis_to__team_match__match=match)

        team_match_a = Team_match.objects.filter(match=match)[0]
        team_match_b = Team_match.objects.filter(match=match)[1]
        player_a = Player_match.objects.filter(team_match=team_match_a)
        player_b = Player_match.objects.filter(team_match=team_match_b)
        points_a = Point.objects.filter(team_match=team_match_a)
        points_b = Point.objects.filter(team_match=team_match_b)
        penalties_a = Penalties.objects.filter(team_match=team_match_a)
        penalties_b = Penalties.objects.filter(team_match=team_match_b)
        match_referee = Match_referee.objects.filter(match=match)
        
        group_phases = Group_phase.objects.filter(phase__event__event=match.event)
        player_match = Player_match.objects.filter(match=match)
        team_match = Team_match.objects.filter(match=match)
        sports = Event_sport.objects.filter(event=match.event)
        status = Status.choices
        detailed = Detailed.choices
        sexos = Sexo_types.choices

        context = {
            'match': match,
            'player_a': player_a,
            'player_b': player_b,
            'points_a': points_a,
            'points_b': points_b,
            'penalties_a': penalties_a,
            'penalties_b': penalties_b,
            'team_match_a': team_match_a,
            'team_match_b': team_match_b,
            'time_pauses': time_pauses,
            'assistance': assistance,
            'match_referee': match_referee,

            'players_match': player_match,
            'teams_match': team_match,
            'group_phases': group_phases,
            'sports': sports,
            'status': status,
            'detailed': detailed,
            'sexos': sexos,
        }
        if match.sport in [1, 2]: 
            context['volley_matchs'] = Volley_match.objects.filter(event=match.event)

        return render(request, 'match_settings.html', context)
    else:
        if 'pauses_delete' in request.POST:
            pause = Time_pause.objects.get(id=request.POST.get('pauses_delete'))
            pause.delete()
        elif 'penalties_delete' in request.POST:
            penalties = Penalties.objects.get(id=request.POST.get('penalties_delete'))
            penalties.delete()
        elif 'point_delete' in request.POST:
            point = Point.objects.get(id=request.POST.get('point_delete'))
            point.delete()
        elif 'assistance_delete' in request.POST:
            assistance = Assistance.objects.get(id=request.POST.get('assistance_delete'))
            assistance.delete()
        elif 'referee_delete' in request.POST:
            referee = Match_referee.objects.get(id=request.POST.get('referee_delete'))
            referee.delete()
        elif 'sumula' in request.POST:
            match_referee = Match_referee.objects.filter(match=match)
            team_match = Team_match.objects.filter(match=match)
            players_match_a = Player_match.objects.filter(team_match=team_match[0])
            players_match_b = Player_match.objects.filter(team_match=team_match[1])
            team_sport_a = Team_sport.objects.get(team=team_match[0].team, sport__sport=team_match[0].match.sport, sexo=team_match[0].match.sexo)
            team_sport_b = Team_sport.objects.get(team=team_match[1].team, sport__sport=team_match[1].match.sport, sexo=team_match[1].match.sexo)
            point_a = Point.objects.filter(team_match=team_match[0])
            point_b = Point.objects.filter(team_match=team_match[1])
            replacements = Replacement.objects.filter(team_match__match=match)
            players_a = [
                {
                'name': i.player.name,
                'number': i.player_number,
                'card_r': Penalties.objects.filter(player=i.player, team_match=team_match[0], type_penalties=0).count(),
                'card_y': Penalties.objects.filter(player=i.player, team_match=team_match[0], type_penalties=1).count(),
                'point': Point.objects.filter(player=i.player, team_match=team_match[0]).count(),
                }
                for i in players_match_a
            ]
            players_b = [
                {
                'name': i.player.name,
                'number': i.player_number,
                'card_r': Penalties.objects.filter(player=i.player, team_match=team_match[0], type_penalties=0).count(),
                'card_y': Penalties.objects.filter(player=i.player, team_match=team_match[0], type_penalties=1).count(),
                'point': Point.objects.filter(player=i.player, team_match=team_match[0]).count(),
                }
                for i in players_match_b
            ]

            authenticity = generate_authenticity(f"Súmula gerada por {request.user.username} da partida entre {team_match[0].team.name} e {team_match[1].team.name}", match.event)
            link = f"https://{request.get_host()}/autenticar?code={authenticity.code}"
            qr = qrcode.make(link)
            buffer = BytesIO()
            qr.save(buffer, format='PNG')
            buffer.seek(0)

            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            context = {
                'match':match,
                'team_match_a':team_match[0],
                'team_match_b':team_match[1],
                'players_a':players_a,
                'players_b':players_b,
                'team_sport_a':team_sport_a,
                'team_sport_b':team_sport_b,
                'point_a':point_a,
                'point_b':point_b,
                'replacements': replacements,
                'user': request.user,
                'match_referee': match_referee,
                'authenticity': authenticity,
                'qr_code': img_base64,
                'logo_ifs': request.build_absolute_uri('/static/images/logo-ifs-black.svg'),
                'logo_morea': request.build_absolute_uri('/static/images/logo-morea.svg'),
                
            }
            html_string = render_to_string('generator/sumula.html', context)

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="sumula-{authenticity.number}.pdf"'
            #response['Content-Disposition'] = f'attachment; filename="sumula.pdf"'

            HTML(string=html_string).write_pdf(response)

            return response
        elif 'location' in request.POST or 'add' in request.POST or 'winner' in request.POST:
            if request.POST.get('sport'): match.sport = int(request.POST.get('sport'))
            if request.POST.get('sexo'): match.sexo = int(request.POST.get('sexo'))
            if request.POST.get('status'): match.status = int(request.POST.get('status'))
            if request.POST.get('detailed'): match.detailed = int(request.POST.get('detailed'))
            if request.POST.get('mvp'): match.mvp_player_player = Player.objects.get(id=request.POST.get('mvp'))
            else: match.mvp_player_player = None
            if request.POST.get('winner'): match.Winner_team = Team.objects.get(id=request.POST.get('winner')) 
            else: match.Winner_team = None
            if request.POST.get('group_phase'): match.group_phase = Group_phase.objects.get(id=request.POST.get('group_phase'))
            if request.POST.get('volley_match'): match.volley_match = Volley_match.objects.get(id=request.POST.get('volley_match'))
            if request.POST.get('time_match'): match.time_match = request.POST.get('time_match')
            if request.POST.get('time_start'): match.time_start = request.POST.get('time_start')
            if request.POST.get('time_end'): match.time_end = request.POST.get('time_end')
            if request.POST.get('location'): match.location = request.POST.get('location')

            if request.POST.get('add'): match.add = request.POST.get('add')
            if request.POST.get('observations'): match.observations = request.POST.get('observations')
            match.save()
        if current_get_params:
            return redirect(f"{reverse('match_settings', args=[id_sport, id_match])}?{current_get_params}")
        else:
            return redirect('match_settings', match.sport, match.id)

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.change_player_match', raise_exception=True)
@permission_required('app.add_player_match', raise_exception=True)
def players_in_teams(request, id):
    match = get_object_or_404(Match, id=id)
    if not _acesso_match(request.user, match):
        messages.error(request, "Você não tem permissão para acessar esta partida.")
        return redirect('games')
    team_match = Team_match.objects.filter(match=match)
    team_match_a = Team_match.objects.get(id=team_match[0].id)
    team_match_b = Team_match.objects.get(id=team_match[1].id)
    team_sport_a = Team_sport.objects.get(team=team_match_a.team, sport=team_match_a.match.sport, sexo=match.sexo)
    team_sport_b = Team_sport.objects.get(team=team_match_b.team, sport=team_match_b.match.sport, sexo=match.sexo)
    player_team_sport_a = Player_team_sport.objects.filter(team_sport=team_sport_a)
    player_team_sport_b = Player_team_sport.objects.filter(team_sport=team_sport_b)
    for i in player_team_sport_a:
        if not Player_match.objects.filter(player=i.player, match=match, team_match=team_match_a).exists():
            Player_match.objects.create(player=i.player, match=match, team_match=team_match_a)
    for i in player_team_sport_b:
        if not Player_match.objects.filter(player=i.player, match=match, team_match=team_match_b).exists():
            Player_match.objects.create(player=i.player, match=match, team_match=team_match_b)
    player_match_a = Player_match.objects.filter(match=match, team_match=team_match_a)
    player_match_b = Player_match.objects.filter(match=match, team_match=team_match_b)
    context = {
        'player_match_a':player_match_a,
        'player_match_b':player_match_b,
        'team_match_a':team_match_a,
        'team_match_b':team_match_b,
        
    }
    if request.method == "GET":
        return render(request, 'players_in_teams.html', context)
    else:
        if 'player_delete' in request.POST:
            if request.user.has_perm('app.delete_player_match'):
                player_id = request.POST.get('player_delete')
                player = Player_match.objects.get(id=player_id)
                player.delete()
            else:
                messages.error(request, "Você não tem permissão para remover o atleta da partida.")
        if 'team-a' in request.POST:
            for i in player_match_a:
                number = request.POST.get(f'number_a_{i.id}')        
                player = get_object_or_404(Player_match, id=i.id) 
                if number != '': 
                    if int(number) >= 0:
                        player.player_number = number
                player.save()
            messages.success(request, f"O número dos atletas do campus {team_match_a.team.get_campus_display()} foram adicionados/atualizados com sucesso!")
        if 'team-b' in request.POST:
            for i in player_match_b:
                number = request.POST.get(f'number_b_{i.id}')          
                player = get_object_or_404(Player_match, id=i.id)
                if number != '': 
                    if int(number) >= 0:
                        player.player_number = number
                player.save()
            messages.success(request, f"O número dos atletas do campus {team_match_b.team.get_campus_display()} foram adicionados/atualizados com sucesso!")
        return redirect('players_in_teams', match.id)

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.change_player_match', raise_exception=True)
@permission_required('app.view_player_match', raise_exception=True)
def players_match(request, id):
    team_match = get_object_or_404(Team_match, id=id)
    player_match = Player_match.objects.filter(team_match=team_match)
    context = {
        'team_match': team_match,
        'player_match': player_match,
        
    }
    if request.method == "GET":
        return render(request, 'manage_players_match.html', context)
    else:
        try:
            players = request.POST.getlist('input-checkbox')
            select_action = request.POST.get('select-action')
            if 'select-action' in request.POST:
                if select_action == 'reserva':
                    for i in players:
                        player = get_object_or_404(Player, id=i)
                        player_match_status = Player_match.objects.get(player=player, team_match=team_match)
                        player_match_status.activity = 1
                        player_match_status.save()
                    return redirect('players_match', team_match.id)
                if select_action == 'titular':
                    for i in players:
                        player = get_object_or_404(Player, id=i)
                        player_match_status = Player_match.objects.get(player=player, team_match=team_match)
                        player_match_status.activity = 0
                        player_match_status.save()
                    return redirect('players_match', team_match.id)
                if select_action == 'excluir':
                    for i in players:
                        player = get_object_or_404(Player, id=i)
                        player_match = Player_match.objects.get(player=player, team_match=team_match)
                        player_match.delete()
                    return redirect('players_match', team_match.id)
            if 'player_match_delete' in request.POST:
                pass
                player_match_id = request.POST.get('player_match_delete')
                player_match = Player_match.objects.get(id=player_match_id)
                player_match.delete()
                return redirect('players_match', team_match.id)
        except (Player.DoesNotExist, Player_match.DoesNotExist):
        except Exception as e:
        return redirect('players_match', team_match.id)

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.change_player_match', raise_exception=True)
@permission_required('app.add_player_match', raise_exception=True)
@permission_required('app.view_player', raise_exception=True)
def add_players_match(request, id):
    team_match = get_object_or_404(Team_match, id=id)
    players = Player.objects.all()
    context = {
        'players': players,
        
    }
    if request.method == "GET":
        return render(request, 'add_players_match.html',context)
    else:
        try:
            player_id = request.POST.getlist('input-checkbox')
            for i in player_id:
                number = request.POST.get(f'number_{i}')
                if int(number) < 1:
                    messages.error(request, "Os números precisam ser maior que 1!")
                    return redirect('add_players_match', id)
                else:
                    player = get_object_or_404(Player, id=i)
                    player_match = Player_match.objects.create(match=team_match.match, team_match=team_match ,player=player, player_number=number)
                    player_match.save()
        except ValueError:
            messages.error(request, "Você precisa informar os jogadores e seus respectivos números corretamente!")
            return redirect('add_players_match', id)

        return redirect('players_match', id)
