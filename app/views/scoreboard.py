"""
Views extraídas automaticamente do views.py monolítico.
Módulo: scoreboard.py
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
@permission_required('app.view_match', raise_exception=True)
@permission_required('app.add_point', raise_exception=True)
@permission_required('app.add_penalties', raise_exception=True)
def scoreboard(request, event_id):  
    match_event = Event.objects.get(id=event_id)
    referee = Voluntary.objects.filter(event=match_event, type_voluntary=6)
    types_referee = Type_referee.choices
    time_now = time.strftime("%H:%M:%S", time.localtime())
    
    if Match.objects.filter(status=1, event=match_event):
        time_now2 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        match = Match.objects.get(status=1, event=match_event)
        match_referee = Match_referee.objects.filter(match=match)
        matches = Match.objects.filter(status=0, event=match_event)
        team_match_all = Team_match.objects.filter(team__event=match_event)
        team_matchs = Team_match.objects.filter(match=match)
        team_match_a = team_matchs[0]
        team_match_b = team_matchs[1]
        banners = Banner.objects.all()
        players_match_a = Player_match.objects.filter(team_match=team_match_a)
        players_match_b = Player_match.objects.filter(team_match=team_match_b)  
        team_sport_a = Team_sport.objects.get(team=team_match_a.team, sport__sport=team_match_a.match.sport, sexo=match.sexo)
        team_sport_b = Team_sport.objects.get(team=team_match_b.team, sport__sport=team_match_b.match.sport, sexo=match.sexo)
        player_team_sport_a = Player_team_sport.objects.filter(team_sport=team_sport_a)
        player_team_sport_b = Player_team_sport.objects.filter(team_sport=team_sport_b)
        seconds, status = generate_timer(match)
        for i in player_team_sport_a:
            if not Player_match.objects.filter(player=i.player, match=match, team_match=team_match_a).exists():
                Player_match.objects.create(player=i.player, match=match, team_match=team_match_a)
        for i in player_team_sport_b:
            if not Player_match.objects.filter(player=i.player, match=match, team_match=team_match_b).exists():
                Player_match.objects.create(player=i.player, match=match, team_match=team_match_b)
        for i in players_match_a:
            if not Player_team_sport.objects.filter(player=i.player, team_sport=team_sport_a).exists():
                i.delete()
        for i in players_match_b:
            if not Player_team_sport.objects.filter(player=i.player, team_sport=team_sport_b).exists():
                i.delete()
        if match.sport == 0:
            point_a = Point.objects.filter(team_match=team_match_a).count() - Point.objects.filter(point_types=2,team_match=team_match_a).count()
            point_b = Point.objects.filter(team_match=team_match_b).count() - Point.objects.filter(point_types=2,team_match=team_match_b).count()
        else:      
            point_a = Point.objects.filter(team_match=team_match_a).count()
            point_b = Point.objects.filter(team_match=team_match_b).count()
    if request.method == "GET":
        context = {
            'event': match_event,
            'point_types': Point_types.choices,
            'penalities_types': Type_penalties.choices,
            'match': match,
            'team_match_a': team_match_a,
            'team_match_b': team_match_b,
            'point_a': point_a,
            'point_b': point_b,
            'players_match_a': players_match_a,
            'players_match_b': players_match_b,
            'points': Point.objects.all(),
            'activity_types': Activity.choices,
            'occurrence': Occurrence.objects.order_by('-id')[:7],
            'seconds': seconds,
            'status': status,
            'banners': banners,
            'matches': matches,
            'team_match_all': team_match_all,
            'detailed': Detailed.choices,
            'referee': referee,
            'types_referee': types_referee,
            'match_referee': match_referee,

        }
        return render(request, 'scoreboard.html', context)
    else:
        if 'detailed' in request.POST:
            try:
                detailed = int(request.POST.get('detailed'))
                match.detailed = detailed
                match.save()
            except (ValueError, TypeError):
                messages.error(request, "Valor de detalhe inválido.")
        elif 'team-a' in request.POST:
            for i in players_match_a:
                number = request.POST.get(f'number_a_{i.id}') 
                activity = request.POST.get(f'activity_a_{i.id}')        
                player = get_object_or_404(Player_match, id=i.id) 
                if number != '': 
                    if int(number) >= 0:
                        player.player_number = number
                        player.activity = int(activity)
                player.save()
            messages.success(request, f"Dados atualizados!")
        elif 'team-b' in request.POST:
            for i in players_match_b:
                number = request.POST.get(f'number_b_{i.id}')   
                activity = request.POST.get(f'activity_b_{i.id}')           
                player = get_object_or_404(Player_match, id=i.id)
                if number != '': 
                    if int(number) >= 0:
                        player.player_number = number
                        player.activity = int(activity)
                player.save()
            messages.success(request, f"Dados atualizados!")
        elif 'assistance' in request.POST:
            point = Point.objects.get(id=request.POST.get('point'))
            player = Player_match.objects.get(id=request.POST.get('player_id'))
            Assistance.objects.create(assis_to=point, player=player)
        elif 'banner' in request.POST:
            banner = Banner.objects.get(id=request.POST.get('banner'))
            if banner.status == 0: 
                banner.status = 1
            else: 
                if Banner.objects.filter(status=0):
                    banners = Banner.objects.filter(status=0)
                    for i in banners:
                        i.status = 1
                        i.save()
                banner.status = 0
            banner.save()

        elif 'replacement_init' in request.POST:
            player_init = get_object_or_404(Player_match, id=request.POST.get("replacement_init"))
            player_end = get_object_or_404(Player_match, id=request.POST.get("replacement_end"))
            player_init.activity = int(player_end.activity)
            player_end.activity = 1
            Replacement.objects.create(team_match=player_init.team_match, player_entry=player_init, player_exit=player_end)
            player_init.save(), player_end.save()
        elif 'referee' in request.POST:
            referee = Voluntary.objects.get(id=request.POST.get("referee"))
            referee_type = int(request.POST.get("type_referee"))
            Match_referee.objects.create(match=match, referee=referee, role=referee_type)
        elif 'color_a' in request.POST or 'color_b' in request.POST:
            if request.POST.get("color_a"):
                team_match_a.team.color = str(request.POST.get("color_a"))
                team_match_a.team.save()
            if request.POST.get("color_b"):
                team_match_b.team.color = str(request.POST.get("color_b"))
                team_match_b.team.save()
        elif 'observations' in request.POST:
            match.observations = request.POST.get("observations")
            match.save()
        elif 'penalties' in request.POST:
            penalties_type = request.POST.get('penalties')
            player_match = Player_match.objects.get(id=request.POST.get('player_penalties'))
            penalties = Penalties.objects.create(player=player_match.player, type_penalties=int(penalties_type), team_match=player_match.team_match)
            penalties.save()
            
            details = f"{player_match.player.name} recebeu {penalties.get_type_penalties_display().lower()}"
            Occurrence.objects.create(name=penalties.get_type_penalties_display(), details=details, match=match)
        elif 'team-a-point' in request.POST:
            if match.sport == 0: type = 0
            else: type = 1
            if request.POST.get("team-a-point") == "+1":
                if request.POST.get("player-a-point"):
                    player = Player.objects.get(id=request.POST.get("player-a-point"))
                    point = Point.objects.create(team_match=team_match_a, player=player, point_types=type)
                    details = f"{player.name} fez um {point.get_point_types_display().lower()}"
                    Occurrence.objects.create(name=point.get_point_types_display(), details=details, match=match)
                else: 
                    point = Point.objects.create(team_match=team_match_a, point_types=type)
                point.save()
            elif Point.objects.filter(team_match=team_match_a, point_types=type).exists(): 
                point = Point.objects.filter(team_match=team_match_a, point_types=type).last().delete()
        elif 'team-b-point' in request.POST:
            if match.sport == 0: type = 0
            else: type = 1
            if request.POST.get("team-b-point") == "+1":
                if request.POST.get("player-b-point"):
                    player = Player.objects.get(id=request.POST.get("player-b-point"))
                    point = Point.objects.create(team_match=team_match_b, player=player, point_types=type)
                    details = f"{player.name} fez um {point.get_point_types_display().lower()}"
                    Occurrence.objects.create(name=point.get_point_types_display(), details=details, match=match)
                else: 
                    point = Point.objects.create(team_match=team_match_b, point_types=type)
                point.save()
            elif Point.objects.filter(team_match=team_match_b, point_types=type).exists(): 
                point = Point.objects.filter(team_match=team_match_b, point_types=type).last().delete()
        elif 'team-a-aces' in request.POST:
            if request.POST.get("team-a-aces") == "+1":
                if request.POST.get("player-a-point"):
                    player = Player.objects.get(id=request.POST.get("player-a-point"))
                    point = Point.objects.create(team_match=team_match_a, player=player, point_types=2)
                    details = f"{player.name} fez um {point.get_point_types_display().lower()}"
                    Occurrence.objects.create(name=point.get_point_types_display(), details=details, match=match)
                else: 
                    point = Point.objects.create(team_match=team_match_a, point_types=2)
                point.save()
            elif Point.objects.filter(team_match=team_match_a, point_types=2).exists(): 
                point = Point.objects.filter(team_match=team_match_a, point_types=2).last().delete()
        elif 'team-b-aces' in request.POST:
            if request.POST.get("team-b-aces") == "+1":
                if request.POST.get("player-b-point"):
                    player = Player.objects.get(id=request.POST.get("player-b-point"))
                    point = Point.objects.create(team_match=team_match_b, player=player, point_types=2)
                    details = f"{player.name} fez um {point.get_point_types_display().lower()}"
                    Occurrence.objects.create(name=point.get_point_types_display(), details=details, match=match)
                else: 
                    point = Point.objects.create(team_match=team_match_b, point_types=2)
                point.save()
            elif Point.objects.filter(team_match=team_match_b, point_types=2).exists(): 
                point = Point.objects.filter(team_match=team_match_b, point_types=2).last().delete()
        elif 'volley_new' in request.POST:
            if match.volley_match and match.status == 1:
                volley_match = Volley_match.objects.get(status=1)
                match.status = 2
                if point_a > point_b:
                    match.Winner_team = team_match_a.team
                    volley_match.sets_team_a += 1
                elif point_b > point_a:
                    match.Winner_team = team_match_b.team
                    volley_match.sets_team_b += 1
                match.save()
                volley_match.save()
                new_match = Match.objects.create(sport=1, sexo=match.sexo, event=match.event, status=5, volley_match=volley_match, time_match=time_now2)
                if match.location:
                    new_match.location = match.location
                if match.group_phase:
                    new_match.group_phase = match.group_phase
                new_match.save()
                team_a_match = Team_match.objects.create(match=new_match, team=team_match_a.team)
                team_a_match.save()
                team_b_match = Team_match.objects.create(match=new_match, team=team_match_b.team)
                team_b_match.save()
                new_match.status = 1
                new_match.save()
                for i in players_match_a:
                    player_match = Player_match.objects.create(match=new_match, team_match=team_a_match ,player=i.player, player_number=i.player_number, activity=i.activity)
                    player_match.save()
                for i in players_match_b:
                    player_match = Player_match.objects.create(match=new_match, team_match=team_b_match ,player=i.player, player_number=i.player_number, activity=i.activity)
                    player_match.save()
                return redirect('scoreboard', match_event.id)
            else:
                messages.error(request, 'OS SETS SÓ PODEM SER CRIADOS EM ESPORTES QUE NECESSITAM DELE. EX: VOLEIBOL')
                return redirect('scoreboard', match_event.id)
            
        elif 'finally' in request.POST:
            if match.time_start and not match.time_end:
                messages.error(request, "Antes de finalizar a partida e iniciar outra você precisa primeiro parar o cronometro!")
                return redirect('scoreboard', match_event.id)
            if Volley_match.objects.filter(status=1) or match.sport in [1,2]:
                volley_match = get_object_or_404(Volley_match, status=1)
                match.status = 2
                match.detailed = 3
                if point_a > point_b:
                    match.Winner_team = team_match_a.team
                    volley_match.sets_team_a += 1
                elif point_b > point_a:
                    match.Winner_team = team_match_b.team
                    volley_match.sets_team_b += 1
                match.save()
                volley_match.status= 2 
                volley_match.save()
            else:
                match.status = 2
                if point_a > point_b:
                    match.Winner_team = team_match_a.team
                elif point_b > point_a:
                    match.Winner_team = team_match_b.team
                match.save()

            return redirect('games')
        elif 'match_new' in request.POST:
            if match.time_start and not match.time_end:
                messages.error(request, "Antes de finalizar a partida e iniciar outra você precisa primeiro parar o cronometro!")
                return redirect('scoreboard', match_event.id)
            next_match_id = request.POST.get('match_new')
            next_match = Match.objects.get(id=next_match_id)
            if match.sport in [1,2]:
                volley_match = get_object_or_404(Volley_match, status=1)
                match.status = 2
                match.detailed = 3
                if point_a > point_b:
                    match.Winner_team = team_match_a.team
                    volley_match.sets_team_a += 1
                elif point_b > point_a:
                    match.Winner_team = team_match_b.team
                    volley_match.sets_team_b += 1
                match.save()
                volley_match.status = 2 
                volley_match.save()
            else:
                match.status = 2
                match.detailed = 3
                if point_a > point_b:
                    match.Winner_team = team_match_a.team
                elif point_b > point_a:
                    match.Winner_team = team_match_b.team
                match.save()
            if next_match.volley_match:
                volley_match = Volley_match.objects.get(id=next_match.volley_match.id)
                volley_match.status = 1
                volley_match.save()
            else:
            team_matchs = Team_match.objects.filter(match=next_match)
            if team_matchs[0] and team_matchs[1]:
                if team_matchs[0].team.photo and team_matchs[1].team.photo:
                    next_match.status = 1
                    next_match.save()
                    return redirect('scoreboard', match_event.id)
            else:
                messages.error(request, "É necessário que tenha 2 times!")
                next_match.status = 3
                next_match.save()
                return redirect('scoreboard', match_event.id)
        elif 'time_init' in request.POST:
            if match.time_start and match.time_end:
                return redirect('scoreboard', match_event.id)
            
            elif match.time_start:
                if Time_pause.objects.filter(match=match):
                    pause = Time_pause.objects.filter(match=match).last()
                    if pause.start_pause and not pause.end_pause:
                        pause.end_pause = time_now
                        pause.save()
                        match.detailed = 1
                        match.save()
                        return redirect('scoreboard', match_event.id)                
                    else:
                        pause_time = Time_pause.objects.create(start_pause=time_now,match=match)
                        pause_time.save()
                        match.detailed = 2
                        match.save()
                        return redirect('scoreboard', match_event.id)
                else:
                    pause_time = Time_pause.objects.create(start_pause=time_now,match=match)
                    pause_time.save()
                    match.detailed = 2
                    match.save()
                    return redirect('scoreboard', match_event.id)
            
            else:
                match.time_start = time_now
                match.save()
                match.detailed = 1
                match.save()
                return redirect('scoreboard', match_event.id)
                
        elif 'time_stop' in request.POST:
            if match.time_start and match.time_end:
                return redirect('scoreboard', match_event.id)
            elif match.time_start:
                if Time_pause.objects.filter(match=match).last():
                    pause = Time_pause.objects.filter(match=match).last()
                    if pause.start_pause and not pause.end_pause:
                        pause.end_pause = time_now
                        pause.save()
                match.time_end = time_now
                match.detailed = 3
                match.save()
                return redirect('scoreboard', match_event.id)
            else:
                return redirect('scoreboard', match_event.id)
        return redirect('scoreboard', match_event.id)

def scoreboard_public(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
        match = None
        if Volley_match.objects.filter(status=1, event=event).exists():
            volley_match = Volley_match.objects.get(status=1, event=event)
            if Match.objects.filter(volley_match=volley_match, status=1, event=event).exists():
                match = Match.objects.get(volley_match=volley_match, status=1, event=event)
        elif Match.objects.filter(status=1, event=event):
            match = Match.objects.get(status=1, event=event)
        if match:
            seconds, status = generate_timer(match)
            team_matchs = Team_match.objects.filter(match=match)

            if match.volley_match:
                if (match.volley_match.sets_team_a + match.volley_match.sets_team_b) % 2 == 0:
                    team_match_a = team_matchs[0]
                    team_match_b = team_matchs[1]
                    sets_a = match.volley_match.sets_team_a
                    sets_b = match.volley_match.sets_team_b
                else:
                    team_match_a = team_matchs[1]
                    team_match_b = team_matchs[0]
                    sets_b = match.volley_match.sets_team_a
                    sets_a = match.volley_match.sets_team_b
                ball_sport = static('images/ball-of-volley.png')
            else:
                team_match_a = team_matchs[0]
                team_match_b = team_matchs[1]
                if match.sport == 3: ball_sport = static('images/ball-of-handball.png')
                else: ball_sport = static('images/ball-of-futsal.png')

            players_match_a = Player_match.objects.filter(team_match=team_match_a)
            players_match_b = Player_match.objects.filter(team_match=team_match_b)
            if match.sport == 0:
                point_a = Point.objects.filter(team_match=team_match_a).count() - Point.objects.filter(point_types=2,team_match=team_match_a).count()
                point_b = Point.objects.filter(team_match=team_match_b).count() - Point.objects.filter(point_types=2,team_match=team_match_b).count()
            else:
                point_a = Point.objects.filter(team_match=team_match_a).count()
                point_b = Point.objects.filter(team_match=team_match_b).count()
            card_a = Penalties.objects.filter(type_penalties=0, team_match=team_match_a).count() + Penalties.objects.filter(type_penalties=1, team_match=team_match_a).count()
            card_b = Penalties.objects.filter(type_penalties=0, team_match=team_match_b).count() + Penalties.objects.filter(type_penalties=1, team_match=team_match_b).count()
            lack_a = Penalties.objects.filter(type_penalties=2,team_match=team_match_a).count()
            lack_b = Penalties.objects.filter(type_penalties=2,team_match=team_match_b).count()
            
            occurrence = Occurrence.objects.filter(match=match).order_by('-datetime')[:10]
            context = {
                'match': match,
                'team_match_a':team_match_a,
                'team_match_b':team_match_b,
                'players_match_a':players_match_a,
                'players_match_b':players_match_b,
                'point_a':point_a,
                'point_b':point_b,
                'lack_a':lack_a,
                'lack_b':lack_b,
                'ball_sport': ball_sport,
                'card_a': card_a,
                'card_b': card_b,
                'events': occurrence,
                'event':event,
            }
            if match.volley_match:
                context['aces_a'] = Point.objects.filter(point_types=2,team_match=team_match_a).count()
                context['aces_b'] = Point.objects.filter(point_types=2,team_match=team_match_b).count()
                context['sets_a'] = sets_a
                context['sets_b'] = sets_b
            else:
                context['seconds'] = seconds
                context['status'] = status
            if match.sport == 0:
                context['penalties_a'] = Point.objects.filter(point_types=2,team_match=team_match_a).count()
                context['penalties_b'] = Point.objects.filter(point_types=2,team_match=team_match_b).count()
            return render(request, 'public/scoreboard_public.html', context)
        else:
            return render(request, 'public/scoreboard_public.html',{'event':event})
    except Exception as e:
        messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return render(request, 'public/scoreboard_public.html',{'event':event})

import qrcode
from io import BytesIO
import base64

def scoreboard_projector(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
        url = request.get_host()

        qr = qrcode.make(url)

        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        if Volley_match.objects.filter(status=1, event=event):
            volley_match = Volley_match.objects.get(status=1, event=event)
            match = Match.objects.filter(volley_match=volley_match.id, event=event).last()
            team_matchs = Team_match.objects.filter(match=match)
            team_match_a = team_matchs[0]
            team_match_b = team_matchs[1]
            if (match.volley_match.sets_team_a + match.volley_match.sets_team_b) % 2 == 0:
                teammatch1 = team_match_a
                teammatch2 = team_match_b
                sets_1 = match.volley_match.sets_team_a
                sets_2 = match.volley_match.sets_team_b
            else:
                teammatch1 = team_match_b
                teammatch2 = team_match_a
                sets_1 = match.volley_match.sets_team_b
                sets_2 = match.volley_match.sets_team_a
            if Banner.objects.filter(status=0): 
                banner_score = Banner.objects.get(status=0).image.url
                banner_bol = True
            else: 
                banner_score = static('images/logo-morea.svg')
                banner_bol = False
            players_match_a = Player_match.objects.filter(team_match=teammatch1)
            players_match_b = Player_match.objects.filter(team_match=teammatch2)
            point_a = Point.objects.filter(team_match=teammatch1).count()
            point_b = Point.objects.filter(team_match=teammatch2).count()
            aces_a = Point.objects.filter(point_types=2,team_match=teammatch1).count()
            aces_b = Point.objects.filter(point_types=2,team_match=teammatch2).count()
            lack_a = Penalties.objects.filter(type_penalties=2,team_match=teammatch1).count()
            lack_b = Penalties.objects.filter(type_penalties=2,team_match=teammatch2).count()
            card_a = Penalties.objects.filter(type_penalties=0,team_match=teammatch1).count() + Penalties.objects.filter(type_penalties=1,team_match=teammatch1).count()
            card_b = Penalties.objects.filter(type_penalties=0,team_match=teammatch2).count() + Penalties.objects.filter(type_penalties=1,team_match=teammatch2).count()
            occurrence = Occurrence.objects.filter()
            name_scoreboard = 'Sets'
            ball_sport = static('images/ball-of-volley.png')
            if match.sexo == 1: 
                img_sexo = static('images/icon-female.svg')
                sexo_color = '#ff32aa' 
            else: 
                img_sexo = static('images/icon-male.svg')
                sexo_color = '#3a7bd5'
            context = {
                'match': match,
                'time_sets_a': sets_1,
                'sets_b': sets_2,
                'team_match_a':teammatch1,
                'team_match_b':teammatch2,
                'players_match_a':players_match_a,
                'players_match_b':players_match_b,
                'point_a':point_a,
                'point_b':point_b,
                'lack_a':lack_a,
                'lack_b':lack_b,
                'img_sexo':img_sexo,
                'sexo_color': sexo_color,
                'ball_sport': ball_sport,
                'aces_a': aces_a,
                'aces_b': aces_b,
                'card_a':card_a,
                'card_b':card_b,
                'colorA': teammatch1.team.color,
                'colorB': teammatch2.team.color,
                'events': occurrence,
                'banner_score':banner_score,
                'banner_bol':banner_bol,
                'sexo_text':match.get_sexo_display(),
                'name_scoreboard': name_scoreboard,
                'qrcode': img_base64,
                'url': url,
                'event': event,
                
                
            }
            return render(request, 'public/scoreboard_projector.html', context)
            
        elif Match.objects.filter(status=1, event=event):
            match = Match.objects.get(status=1, event=event)
            occurrence = Occurrence.objects.filter(match=match)
            team_matchs = Team_match.objects.filter(match=match)
            team_match_a = team_matchs[0]
            team_match_b = team_matchs[1]
            players_match_a = Player_match.objects.filter(team_match=team_match_a)
            players_match_b = Player_match.objects.filter(team_match=team_match_b)
            point_a = Point.objects.filter(team_match=team_match_a).count() - Point.objects.filter(point_types=2,team_match=team_match_a).count()
            point_b = Point.objects.filter(team_match=team_match_b).count() - Point.objects.filter(point_types=2,team_match=team_match_b).count()
            penalties_a = Point.objects.filter(point_types=2,team_match=team_match_a).count()
            penalties_b = Point.objects.filter(point_types=2,team_match=team_match_b).count()
            lack_a = Penalties.objects.filter(type_penalties=2,team_match=team_match_a).count()
            lack_b = Penalties.objects.filter(type_penalties=2,team_match=team_match_b).count()
            card_a = Penalties.objects.filter(type_penalties=0,team_match=team_match_a).count() + Penalties.objects.filter(type_penalties=1,team_match=team_match_a).count()
            card_b = Penalties.objects.filter(type_penalties=0,team_match=team_match_b).count() + Penalties.objects.filter(type_penalties=1,team_match=team_match_b).count()
            seconds, status = generate_timer(match)
            name_scoreboard = 'Tempo'
            if match.sport == 3:
                ball_sport = static('images/ball-of-handball.png')
            else:
                ball_sport = static('images/ball-of-futsal.png')
            if Banner.objects.filter(status=0): 
                banner_score = Banner.objects.get(status=0).image.url
                banner_bol = True
            else: 
                banner_score = static('images/logo-morea.svg')
                banner_bol = False
            context = {
                'match': match,
                'events':occurrence,
                'time_sets_a': "00:00",
                'status': status,
                'seconds': seconds,
                'team_match_a':team_match_a,
                'team_match_b':team_match_b,
                'players_match_a':players_match_a,
                'players_match_b':players_match_b,
                'point_a':point_a,
                'point_b':point_b,
                'penalties_a':penalties_a,
                'penalties_b':penalties_b,
                'lack_a':lack_a,
                'lack_b':lack_b,
                'ball_sport': ball_sport,
                'aces_a': 0,
                'aces_b': 0,
                'colorA': team_match_a.team.color,
                'colorB': team_match_b.team.color,
                'banner_score':banner_score,
                'banner_bol':banner_bol,
                'card_a': card_a,
                'card_b': card_b,
                'sexo_text':match.get_sexo_display(),
                'name_scoreboard': name_scoreboard,
                'qrcode': img_base64,
                'url': url,
                'event': event,
            }
            return render(request, 'public/scoreboard_projector.html', context)
        else:
            return render(request, 'public/scoreboard_projector.html', {'qrcode': img_base64, 'event': event, 'url': url, 'colorA': "#FF0000", 'colorB': "#0000FF"})
    except Exception as e:
        messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return render(request, 'public/scoreboard_projector.html')
