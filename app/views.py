from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, QueryDict
from .models import Sexo_types, Settings_access, UserSession, Campus_types, Help, Type_penalties, Activity, Statement, Point_types, Event, Event_sport, Statement_user, Users_types, Type_service, Certificate, Attachments, Volley_match, Player, Sport_types, Voluntary, Penalties, Occurrence, Time_pause, Team, Point, Team_sport, Player_team_sport, Match, Team_match, Player_match, Assistance,  Banner, Terms_Use
from django.db.models import Count, Q, Prefetch
from .decorators import time_restriction
from django.contrib import messages
from django.db import IntegrityError
from django.templatetags.static import static
from django.contrib.auth.models import User, Group, Permission
from django.contrib.sessions.models import Session
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login as auth_login, authenticate, logout, get_user_model
from django.template.loader import render_to_string
from .forms import Terms_UseForm
from datetime import date, datetime
from reportlab.pdfgen import canvas
from .generators import generate_certificates, generate_badges, generate_events, generate_timer
import time, pytz, os
from django.core.files.base import ContentFile
from weasyprint import HTML
from django.utils import timezone
from .decorators import terms_accept_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse

User = get_user_model()

@login_required(login_url="login")
def events_list(request):
    if request.method == 'GET':
        events = Event.objects.all()
        if len(events) == 1:
            return redirect('home_public', events[0].id)
        return render(request, 'public/events_list.html', {'events': events})
    else:
        return redirect('events')

def has_accepted_terms(user):
    try:
        termo = Terms_Use.objects.get(usuario=user)
        return bool(termo.name and termo.siape and termo.document and termo.photo and termo.accepted)
    except Terms_Use.DoesNotExist:
        return False
        
def page_in_erro404(request):
    return render(request, 'error_404.html', status=404)

def about_us(request, event_id):
    event = Event.objects.get(id=event_id)
    return render(request, 'public/about_us.html',{'event':event})

@login_required(login_url="login")
@permission_required('app.view_event', raise_exception=True)
def event_manage(request):
    if request.method == "GET":
        events = Event.objects.all()
        return render(request, 'events/event_manage.html', {
            'events': events,
            'sports': Sport_types.choices
        })

    else:
        if 'event' in request.POST:
            event_id = request.POST.get('event')
            sport = request.POST.get('sport')
            min_sport = request.POST.get('min_sport')
            max_sport = request.POST.get('max_sport')
            fem = 'fem' in request.POST
            masc = 'masc' in request.POST
            mist = 'mist' in request.POST

            Event_sport.objects.create(
                event=Event.objects.get(id=event_id),
                sport=sport,
                min_sport=min_sport,
                max_sport=max_sport,
                fem=fem,
                masc=masc,
                mist=mist,
            )

        elif 'name' in request.POST:
            name = request.POST.get('name')
            logo = request.FILES.get('logo')
            description = request.POST.get('description')
            date_init = request.POST.get('date_init')
            date_end = request.POST.get('date_end')
            enrollment_init = request.POST.get('enrollment_init')
            enrollment_end = request.POST.get('enrollment_end')
            local = request.POST.get('local')
            age = request.POST.get('age')
            regulation = request.FILES.get('regulation')

            player_need_instagram = 'player_need_instagram' in request.POST
            player_need_photo = 'player_need_photo' in request.POST
            player_need_bulletin = 'player_need_bulletin' in request.POST
            player_need_rg = 'player_need_rg' in request.POST
            player_need_sexo = 'player_need_sexo' in request.POST
            player_need_registration = 'player_need_registration' in request.POST
            player_need_cpf = 'player_need_cpf' in request.POST
            player_need_date_nasc = 'player_need_date_nasc' in request.POST

            Event.objects.create(
                name=name,
                logo=logo,
                description=description,
                date_init=date_init,
                date_end=date_end,
                enrollment_init=enrollment_init,
                enrollment_end=enrollment_end,
                local=local,
                age=age,
                regulation=regulation,
                user=request.user,

                player_need_instagram=player_need_instagram,
                player_need_photo=player_need_photo,
                player_need_bulletin=player_need_bulletin,
                player_need_rg=player_need_rg,
                player_need_sexo=player_need_sexo,
                player_need_registration=player_need_registration,
                player_need_cpf=player_need_cpf,
                player_need_date_nasc=player_need_date_nasc,
                
            )

        return redirect('event_manage')


@login_required(login_url="login")
def event_edit(request):
    return render(request, 'teste.html')

@login_required(login_url="login")
def event_sport_manage(request):
    return render(request, 'events/event_manage.html')

@login_required(login_url="login")
def event_sport_edit(request):
    return render(request, 'events/event_manage.html')

def home_public(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
        hoje = date.today()
        games_day = Match.objects.filter(time_match__date=hoje).prefetch_related('teams__team').order_by('time_match')
        context_games_day = [
            {
                'match': match,
                'times': list(match.teams.all()),
            }
            for match in games_day
        ]


        volei_masc = Volley_match.objects.filter(matches__sexo=0).prefetch_related('matches__teams__team').distinct()
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

        volei_fem = Volley_match.objects.filter(matches__sexo=1).prefetch_related('matches__teams__team').distinct()
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
        
        matchs_futsal_masc = Match.objects.filter(sport=0, sexo=0).prefetch_related('teams__team').order_by('time_match')
        context_futsal_masc = [
            {
                'match': match,
                'times': list(match.teams.all()),
                'points_a': Point.objects.filter(team_match=match.teams.first()).count(),
                'points_b': Point.objects.filter(team_match=match.teams.last()).count(),
            }
            for match in matchs_futsal_masc
        ]

        matchs_futsal_fem = Match.objects.filter(sport=0, sexo=1).prefetch_related('teams__team').order_by('time_match')
        context_futsal_fem = [
            {
                'match': match,
                'times': list(match.teams.all()),
                'points_a': Point.objects.filter(team_match=match.teams.first()).count(),
                'points_b': Point.objects.filter(team_match=match.teams.last()).count(),
            }
            for match in matchs_futsal_fem

        ]

        matchs_handebol_masc = Match.objects.filter(sport=3, sexo=0).prefetch_related('teams__team').order_by('time_match')
        context_handebol_masc = [
            {
                'match': match,
                'times': list(match.teams.all()),
                'points_a': Point.objects.filter(team_match=match.teams.first()).count(),
                'points_b': Point.objects.filter(team_match=match.teams.last()).count(),
            }
            for match in matchs_handebol_masc
        ]

        matchs_handebol_fem = Match.objects.filter(sport=3, sexo=1).prefetch_related('teams__team').order_by('time_match')
        context_handebol_fem = [
            {
                'match': match,
                'times': list(match.teams.all()),
                'points_a': Point.objects.filter(team_match=match.teams.first()).count(),
                'points_b': Point.objects.filter(team_match=match.teams.last()).count(),
            }
            for match in matchs_handebol_fem

        ]

        matchs_queimado_fem = Match.objects.filter(sport=8, sexo=0).prefetch_related('teams__team').order_by('time_match')
        context_queimado_fem = [
            {
                'match': match,
                'times': list(match.teams.all()),
                'points_a': Point.objects.filter(team_match=match.teams.first()).count(),
                'points_b': Point.objects.filter(team_match=match.teams.last()).count(),
            }
            for match in matchs_queimado_fem
        ]

        matchs_queimado_masc = Match.objects.filter(sport=8, sexo=1).prefetch_related('teams__team').order_by('time_match')
        context_queimado_masc = [
            {
                'match': match,
                'times': list(match.teams.all()),
                'points_a': Point.objects.filter(team_match=match.teams.first()).count(),
                'points_b': Point.objects.filter(team_match=match.teams.last()).count(),
            }
            for match in matchs_queimado_masc
        ]




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
            }
            print(context)
            return render(request, 'public/home_public.html', context)
    except Exception as e:
        messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return render(request, 'public/home_public.html',{'event':event})


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

def login(request):
        if request.user.is_authenticated == False:
            if request.method == "GET":
                return render(request, 'login.html')
            else:
                username = request.POST.get('username')
                password = request.POST.get('password')
                user = authenticate(username=username, password=password)
                if user:
                    auth_login(request, user)
                    if user.team:
                        messages.success(request, f"Seja bem-vindo time {user.team.name}! para navegar, acesse o menu.")
                    else:
                        messages.success(request, f"Seja bem-vindo ao sistema {user.username}!")
                    return redirect('Home')
                else:
                    messages.error(request,"Poxa! algo está errado, pode ser o usuário ou a senha.")
                    return redirect('login')
        else:
            return redirect('Home')

@login_required(login_url="login")
@terms_accept_required
def sair(request):
    logout(request)
    return redirect('events')

@login_required(login_url="login")
@terms_accept_required
def attachments(request):
    if request.method == "GET":
        context = {}
        if request.user.type == 0:  context['events'] = Event.objects.all()
        if request.user.type != 0:
            context['attachments'] = Attachments.objects.filter(event=request.user.event_user)
        elif 'e' in request.GET and request.GET.get('e') != '':
            context['attachments'] = Attachments.objects.filter(event__id=request.GET.get('e'))
            context['select_event'] = request.GET.get('e')

        return render(request, 'attachments.html', context)
    else:
        name = request.POST.get('name')
        public = 'public' in request.POST
        file = request.FILES.get('file')
        if request.user.type == 0:
            Attachments.objects.create(name=name, file=file, event=Event.objects.get(id=request.POST.get('event')), public=public)
        else:
            Attachments.objects.create(name=name, file=file, event=request.user.event_user, public=public)
        return redirect("attachments")

def erro_403_customizado(request, exception=None):
    messages.info(request, "Você não tem permissão para acessar essa página. Contate o administrador.")
    return redirect('Home')

def erro_404_customizado(request, exception):
    return render(request, 'public/error_404.html', status=404)

@login_required(login_url="login")
@permission_required('app.view_player', raise_exception=True)
@terms_accept_required
def player_manage(request):
    if request.method == "GET":
        context = {
            'events': Event.objects.all()
        }
        if request.user.type == 1:
            player = Player.objects.filter(event=request.user.event_user).order_by('id')
        elif request.user.type == 2:
            player = Player.objects.filter(event=request.user.event_user, admin=request.user).order_by('id')
        elif 'e' in request.GET and request.GET['e'] != '' and request.GET['e'] != '0':
            event = Event.objects.get(id=request.GET['e'])
            player = Player.objects.filter(event=event).order_by('id')
            context['select_event'] = request.GET['e']
        else:
            if request.user.is_staff:  
                player = Player.objects.all().order_by('-id')
            else:
                player = Player.objects.filter(admin=request.user).order_by('-id')
        page = request.GET.get('page', 1) 
        paginator = Paginator(player, 20) 
        print(player)
        try:
            player_paginated = paginator.page(page)
        except PageNotAnInteger:
            player_paginated = paginator.page(1)
        except EmptyPage:
            player_paginated = paginator.page(paginator.num_pages)
        context['player'] = player_paginated
        return render(request, 'players/player_manage.html', context)
    else:
        try:
            if 'player_delete' in request.POST:
                player_id = request.POST.get('player_delete')
                player_delete = Player.objects.get(id=player_id)
                status = verificar_foto(str(player_delete.photo))
                if status:
                    player_delete.photo.delete()
                player_delete.delete()
                messages.success(request, "Atleta removido com sucesso!")
            return redirect('player_manage')
        except Exception as e: messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return redirect('player_manage')

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.change_player', raise_exception=True)
def player_edit(request, id):
    try:
        campus = Campus_types.choices
        player = get_object_or_404(Player, id=id)
        if request.method == 'GET':
            return render(request, 'players/player_edit.html', {'player': player, 'campus': campus})            
        else:
            print(request.FILES)

            player.name = request.POST.get('name')
            player.sexo = request.POST.get('sexo')
            player.registration = request.POST.get('registration')
            player.cpf = request.POST.get('cpf')
            photo = request.FILES.get('photo')
            print("verifica:")
            if photo:
                print("photo")
                status = type_file(request, ['.png','.jpg','.jpeg'], photo, 'A photo anexada não é do tipo png, jpg ou jpeg, considere converte-la em um desses tipos.')
                if not status:
                    print("status")
                    status_photo = verificar_foto(str(player.photo))
                    if status_photo:
                        player.photo.delete()
                    player.photo = photo
            campus_id = request.POST.get('campus')
            if campus_id:
                player.campus = campus_id
            player.save()
            messages.success(request, "Os dados do atleta foram atualizados com sucesso!")
            return redirect('player_manage')
    except Exception as e: messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
    return redirect('Home')

@time_restriction("team_manage")
@login_required(login_url="login")
@terms_accept_required
@permission_required('app.change_player', raise_exception=True)
def team_players_edit(request, id, team):
    try:
        team_sport = Team_sport.objects.get(id=team)
        campus = Campus_types.choices
        player = get_object_or_404(Player, id=id)
        if request.method == 'GET':
            return render(request, 'team/team_players_edit.html', {'player': player, 'campus': campus, 'team_sport': team_sport})            
        else:
            print(request.FILES)

            player.name = request.POST.get('name')
            player.sexo = request.POST.get('sexo')
            player.registration = request.POST.get('registration')
            player.cpf = request.POST.get('cpf')
            photo = request.FILES.get('photo')
            print("verifica:")
            if photo:
                print("photo")
                status = type_file(request, ['.png','.jpg','.jpeg'], photo, 'A photo anexada não é do tipo png, jpg ou jpeg, considere converte-la em um desses tipos.')
                print(status)
                if not status:
                    print("status")
                    status_photo = verificar_foto(str(player.photo))
                    if status_photo:
                        player.photo.delete()
                    else: print("an?")
                    player.photo = photo
                else: print("nop")
            campus_id = request.POST.get('campus')
            if campus_id:
                player.campus = campus_id
            player.save()
            messages.success(request, "Os dados do atleta foram atualizados com sucesso!")
            return redirect('team_players_manage', team_sport.id)
    except Exception as e: messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
    return redirect('team_manage')

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.view_team_sport', raise_exception=True)
def team_manage(request):
    context = {}

    current_get_params = request.GET.urlencode()

    if request.method == "GET":
        if request.user.type == 0: 
            context['users'] = User.objects.all()
            context['events'] = Event.objects.all()
        

        e = request.GET.get("e")
        t = request.GET.get("t")
        q = request.GET.get("q")

        if q and e and t:
            context['teams'] = Team.objects.filter(event__id=e)
            context['events_sport'] = Event_sport.objects.filter(event__id=e)
            context['team_sports'] = Team_sport.objects.filter(team__id=t)
            context['team'] = Team.objects.get(id=t)
            context['select_event'] = e

        elif e and t:
            context['teams'] = Team.objects.filter(event__id=e)
            context['events_sport'] = Event_sport.objects.filter(event__id=e)
            context['team_sports'] = Team_sport.objects.filter(team__id=t)
            context['team'] = Team.objects.get(id=t)
            context['select_event'] = e

        elif e:
            context['teams'] = Team.objects.filter(event__id=e)
            context['events_sport'] = Event_sport.objects.filter(event__id=e)
            context['select_event'] = e

        elif t and request.user.type == 1:
            context['teams'] = Team.objects.filter(event__id=request.user.event_user.id)
            context['events_sport'] = Event_sport.objects.filter(event__id=request.user.event_user.id)
            context['team'] = Team.objects.get(id=t)
            context['team_sports'] = Team_sport.objects.filter(team__id=t)
            context['users'] = User.objects.filter(event_user=request.user.event_user)

        elif request.user.type == 1:
            print("eita")
            context['teams'] = Team.objects.filter(event__id=request.user.event_user.id)
            context['events_sport'] = Event_sport.objects.filter(event__id=request.user.event_user.id)

        elif request.user.type == 2:
            context['team'] = Team.objects.get(id=request.user.team.id)
            context['team_sports'] = Team_sport.objects.filter(team__id=request.user.team.id)
            context['events_sport'] = Event_sport.objects.filter(event__id=request.user.event_user.id)
            
        print("passou: ", context)
        return render(request, 'team/team_manage.html', context)

    else:
        print(request.POST)
        if 'add-team' in request.POST:
            name = request.POST.get("name")
            description = request.POST.get("description")
            photo = request.FILES.get("photo")
            event = Event.objects.get(id=request.POST.get("add-team"))
            Team.objects.create(name=name, description=description, photo=photo, event=event)
        elif 'add-team-sport' in request.POST:
            team = Team.objects.get(id=request.POST.get("add-team-sport"))
            sport = Event_sport.objects.get(id=request.POST.get("sport_adm_id"))
            sexo = int(request.POST.get("sexo_adm_id"))
            if not Team_sport.objects.filter(team=team, sport=sport, sexo=sexo, event=sport.event):
                if sexo == 0 and not sport.masc or sexo == 1 and not sport.fem or sexo == 2 and not sport.mist:
                    messages.error(request,"O esporte escolhido não está disponível para este sexo. Em caso de dúvidas, consulte o regulamento.")
                else:
                    Team_sport.objects.create(team=team, sport=sport, sexo=sexo, event=sport.event)
                    messages.success(request,"Esporte cadastrado com sucesso, adicione atletas.")
            else:
                messages.info(request,"O esporte já existe, adicione atletas.")
        elif 'edit-team' in request.POST:
            team = Team.objects.get(id=request.POST.get("edit-team"))
            team.name = request.POST.get("edit-name")
            if request.FILES.get("edit-logo"):
                team.photo = request.FILES.get("edit-logo")
            team.description = request.POST.get("edit-description")
            if request.POST.get('edit-status') == 'on': team.status = True
            else: team.status = False
            team.save()

        elif 'team-data' in request.POST:
            team_id = request.POST.get('team-data')
            team = Team.objects.get(id=team_id)
            cont = {
                'now': timezone.now(),
                'team': team,
                'user': request.user,
                'logo_ifs': request.build_absolute_uri('/static/images/logo-jiifs-2025.jpg'),
                'logo_morea': request.build_absolute_uri('/static/images/logo_ifs.png')
            }
            name_html = 'data-base-teams'
            name_pdf = f'relatório do {team.name}'
            
            teams = Team_sport.objects.filter(team=team).prefetch_related(Prefetch('players', queryset=Player_team_sport.objects.select_related('player'))).order_by('sport__sport', '-sexo')

            cont['teams'] = teams
            print(cont)
            html_string = render_to_string(f'generator/{name_html}.html', cont)

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{name_pdf}.pdf"'
            # response['Content-Disposition'] = f'attachment; filename="{name_pdf}.pdf"'
            HTML(string=html_string).write_pdf(response)

            return response
        
        elif 'team_sport_delete' in request.POST:
            team_sport_id = request.POST.get('team_sport_delete')
            team_sport_delete = Team_sport.objects.get(id=team_sport_id)
            players_team_sport = Player_team_sport.objects.filter(team_sport=team_sport_delete)
            print(players_team_sport)
            if players_team_sport:
                for i in players_team_sport:
                    i.delete()     
                    print("apagado player somente do")
                    if not Player_team_sport.objects.filter(player=i.player).exists():
                        
                        print("APAGANDO JOGADOR: ", i.player.name)
                        status = verificar_foto(str(i.player.photo))
                        if status:
                            i.player.photo.delete()
                        i.player.bulletin.delete()
                        i.player.rg.delete()
                        i.player.delete()     
            team_sport_delete.delete()
            if not Team_sport.objects.filter(team=team_sport_delete.team.id):
                pass
                #Team.objects.get(id=team_sport_delete.team.id).delete()

        if current_get_params:
            return redirect(f"{reverse('team_manage')}?{current_get_params}")
        else:
            return redirect('team_manage')

@login_required(login_url="login") 
def theme_manage(request):
    return render(request, 'settings/theme.html')

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.change_team_sport', raise_exception=True)
def team_edit(request, id):
    team_sport = get_object_or_404(Team_sport, id=id)
    sport = Sport_types.choices
    campus = Campus_types.choices
    sexo = Sexo_types.choices
    users = User.objects.all()
    if request.method == 'GET': 
        return render(request, 'team/team_edit.html', {'team_sport': team_sport, 'campus': campus, 'sport': sport, 'sexo': sexo, 'users': users})
    else:
        try:
            team_sport.sport = request.POST.get('sport')
            team_sport.sexo = request.POST.get('sexo')
            team_sport.admin = User.objects.get(id=request.POST.get('user'))
            team_sport.team.campus = request.POST.get('campus')
            for i in campus: 
                if i[0] == int(request.POST.get('campus')): team_sport.team.name = i[1]
            team_sport.team.save() 
            team_sport.save() 
            messages.success(request, 'Alteração feita com sucesso!')
            return redirect('team_manage') 
        except (TypeError, ValueError): messages.error(request, 'Um valor foi informado incorretamente!')
        except IntegrityError as e: messages.error(request, 'Algumas informações não foram preenchidas :(')
        except Exception as e: messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
    return redirect('team_manage') 

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.view_player_team_sport', raise_exception=True)
def team_players_manage(request, id):
        team_sport = get_object_or_404(Team_sport, id=id)
        if len(Player_team_sport.objects.filter(team_sport=team_sport)) >= team_sport.sport.min_sport and team_sport.status == False:
            team_sport.status = True
            team_sport.save()
        elif len(Player_team_sport.objects.filter(team_sport=team_sport)) < team_sport.sport.min_sport and team_sport.status == True:
            team_sport.status = False
            team_sport.save()
        user = User.objects.get(id=request.user.id)
        if request.method == "GET":
            player_team_sport = Player_team_sport.objects.select_related('player', 'team_sport').filter(team_sport=id)     
            return render(request, 'team/team_players_manage.html', {'player_team_sport': player_team_sport,'sexos': Sexo_types.choices,'team_sport': team_sport, 'events': Event.objects.all()})
        else:
            print(request.POST)
            if request.POST.get("player_delete"):
                print(request.POST)
                player = request.POST.get('player_delete')
                Player_team_sport.objects.get(team_sport=id, player=player).delete()
                if not Player_team_sport.objects.filter(player=player).exists():
                    Player.objects.get(id=player).delete()
                if len(Player_team_sport.objects.filter(team_sport=team_sport)) < team_sport.sport.min_sport and team_sport.status == True:
                    team_sport.status = False
                    team_sport.save()
            elif request.POST.get("edit-name"):
                player = Player.objects.get(id=request.POST.get("edit-player-id"))
                player.name = request.POST.get("edit-name")
                player.classroom = request.POST.get('edit-classroom')
                if team_sport.team.event.player_need_registration:
                    player.registration = request.POST.get("edit-registration")
                if team_sport.team.event.player_need_date_nasc:
                    player.date_nasc = request.POST.get("edit-date")
                if team_sport.team.event.player_need_sexo:
                    player.sexo = request.POST.get("edit-sexo")
                if team_sport.team.event.player_need_photo:
                    if request.FILES.get("edit-photo"):
                        player.photo = request.FILES.get("edit-photo")
                if team_sport.team.event.player_need_bulletin:
                    if request.FILES.get("edit-bulletin"):
                        player.bulletin = request.FILES.get("edit-bulletin")
                if team_sport.team.event.player_need_rg:
                    if request.FILES.get("edit-rg"):
                        player.rg = request.FILES.get("edit-rg")
                player.save()
                messages.success(request, "Atleta atualizado com sucesso!")
            elif 'search' in request.POST: 
                print("oiii")
                number_players = len(Player_team_sport.objects.filter(team_sport=team_sport))
                if number_players >= team_sport.sport.max_sport:
                    messages.error(request, "O seu time atingiu o limite de atletas nessa modalidade!")
                    print("O seu time atingiu o limite de atletas nessa modalidade!")
                    return redirect('team_players_manage', team_sport.id)
                qe = request.POST.get('search')
                if request.user.type == 0 or request.user.type == 1:
                    if qe.isdigit(): player_filter = Player.objects.filter(registration=int(qe), event=team_sport.team.event)
                    else: player_filter = Player.objects.filter(name__icontains=qe, event=team_sport.team.event)
                else:
                    if qe.isdigit(): player_filter = Player.objects.filter(registration=int(qe), event=team_sport.team.event, admin=user)
                    else: player_filter = Player.objects.filter(name__icontains=qe, event=team_sport.team.event, admin=user)
                if len(player_filter) > 1:
                    messages.error(request, f"{len(player_filter)} atletas foram encontrados, seja mais preciso, você pode buscar pelo nome e pela matrícula!")
                elif len(player_filter) == 0:
                    messages.error(request, "O atleta não foi encontrado!")
                    return redirect('team_players_manage', team_sport.id)
                else:
                    player = Player.objects.get(id=player_filter.first().id)
                    if not Player_team_sport.objects.filter(player=player, team_sport=team_sport):          
                        Player_team_sport.objects.create(player=player, team_sport=team_sport)        
                        messages.success(request, f"O atleta {player.name} foi cadastrado na modalidade com sucesso!")
                        return redirect('team_players_manage', team_sport.id)
                    else:
                        messages.info(request, f"O atleta {player.name} já está cadastrado, tá?!")
                        return redirect('team_players_manage', team_sport.id)
            elif 'name' in request.POST:
                number_players = len(Player_team_sport.objects.filter(team_sport=team_sport))
                if number_players >= team_sport.sport.max_sport:
                    messages.error(request, "O seu time atingiu o limite de atletas nessa modalidade!")
                    print("O seu time atingiu o limite de atletas nessa modalidade!")
                    return redirect('team_players_manage', team_sport.id)
                if len(Player_team_sport.objects.filter(team_sport=team_sport)) >= team_sport.sport.min_sport and team_sport.status == False:
                    team_sport.status = True
                    team_sport.save()

                if team_sport.team.event.player_need_date_nasc:
                    date_nasc = datetime.strptime(request.POST.get('date'), "%Y-%m-%d")
                    date_today = date.today()
                    if (date_today.year - date_nasc.year) > 19:
                        messages.error(request, "O atleta não pode ser cadastrado por conta da idade :(")
                        print("O atleta não pode ser cadastrado por conta da idade :(")
                        return redirect('team_players_manage', team_sport.id)
                    
                if team_sport.team.event.player_need_photo:
                    photo = request.FILES.get('photo')
                    if photo:
                        status = type_file(request, ['.png','.jpg','.jpeg'], photo, 'A photo anexada não é do tipo png, jpg ou jpeg, considere converte-la em um desses tipos.')
                        if status: return redirect('team_players_manage', team_sport.id)

                if team_sport.team.event.player_need_bulletin:
                    bulletin = request.FILES.get('bulletin')
                    if bulletin: 
                        status = type_file(request, ['.pdf'], bulletin, 'O boletim escolar anexado não é do tipo pdf, que é o tipo aceito.')
                        if status: return redirect('team_players_manage', team_sport.id)
                if team_sport.team.event.player_need_rg:
                    rg = request.FILES.get('rg')
                    if rg: 
                        status = type_file(request, ['.png','.jpg','.jpeg','.pdf','docx'], rg, 'O RG anexado não é faz parte dos tipos aceito, os tipos são png, jpg, jpeg, pdf ou docs.')
                        if status: return redirect('team_players_manage', team_sport.id)

                name = request.POST.get('name')
                print("aleratorio")

                if not Player.objects.filter(name=name, admin=user, event=team_sport.event).exists():
                    player = Player.objects.create(name=name, admin=user, event=team_sport.event)
                    print("criando novo atleta")
                else:
                    player = Player.objects.get(name=name, admin=user, event=team_sport.event)
                player.classroom = request.POST.get('classroom')
                if team_sport.team.event.player_need_date_nasc:
                    player.date_nasc = date_nasc
                if team_sport.team.event.player_need_registration:
                    player.registration = request.POST.get('registration')
                if team_sport.team.event.player_need_cpf:
                    cpf = request.POST.get('cpf')
                    player.cpf = cpf.replace("-","").replace(".","")
                if team_sport.team.event.player_need_photo:
                    player.photo = photo
                if team_sport.team.event.player_need_bulletin:
                    player.bulletin = bulletin
                if team_sport.team.event.player_need_sexo:
                    player.sexo = team_sport.sexo
                if team_sport.team.event.player_need_rg:
                    player.rg = rg
                player.save()

                if not Player_team_sport.objects.filter(player=player, team_sport=team_sport):          
                    Player_team_sport.objects.create(player=player, team_sport=team_sport)        
                    messages.success(request, "O jogador foi cadastrado no sistema com sucesso!")
                    print("O jogador foi cadastrado no sistema com sucesso!")
                else:
                    messages.info(request, "O jogador já está cadastrado nessa modalidade, tá?!")
            return redirect('team_players_manage', team_sport.id)

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.add_player_team_sport', raise_exception=True)
def add_player_team(request, id):
    team = get_object_or_404(Team_sport, id=id)
    players = Player.objects.all()
    if request.method == 'GET':
        if not players: messages.info(request, "Não tem nenhum atleta cadastrado no sistema!")
        return render(request, 'add_players_team.html', {'players': players,'team': team}) 
    else:
        try:
            player = request.POST.getlist('input-checkbox')
            for i in player:
                player = Player.objects.get(id=i)
                Player_team_sport.objects.create(player=player, team_sport=team)
        except (TypeError, ValueError):
            messages.error(request, 'Um valor foi informado incorretamente!')
        except IntegrityError as e:
            messages.error(request, 'Algumas informações não foram preenchidas :(')
        except Exception as e:
            messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return redirect('team_players_manage', team.id)
    
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
                print("Não há nenhuma partida cadastrada!")
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
                print("certin")
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
        contex = {
            'team': Team.objects.all(),
            'sport': Sport_types.choices,
            'events': Event.objects.all(),
        }
        if request.user.type in [1,2]:
            matchs = Match.objects.filter(event=request.user.event_user).prefetch_related('teams__team').order_by('time_match')
        elif 'e' in request.GET and request.GET['e'] != '':
            matchs = Match.objects.filter(event=Event.objects.get(id=request.GET['e'])).prefetch_related('teams__team').order_by('time_match')
            contex['select_event'] = request.GET['e']
        else:
            matchs = Match.objects.all().prefetch_related('teams__team').order_by('time_match')
        context = [
            {
                'match': match,
                'times': list(match.teams.all()),
                'points_a': Point.objects.filter(team_match=match.teams.first()).count(),
                'points_b': Point.objects.filter(team_match=match.teams.last()).count(),
                
            }
            for match in matchs

        ]
        contex['context'] = context
        contex['events'] = Event.objects.all()
        
        return render(request, 'games.html', contex)
    else:
        sport_id = int(request.POST.get('sport'))
        sexo = request.POST.get('sexo')
        team_a_id = request.POST.get('time_a')
        team_b_id = request.POST.get('time_b')
        datetime = request.POST.get('datetime')
        if not request.user.event_user: event = Event.objects.get(id=request.POST.get('event'))
        else: event = request.user.event_user
        if team_a_id == team_b_id:
            messages.error(request, "Você não pode criar uma partida com times iguais!")
            return redirect('matches_register')
        team_a = Team.objects.get(id=team_a_id)
        team_b = Team.objects.get(id=team_b_id)
        if not Team_sport.objects.filter(team=team_a, sexo=sexo).exists() or not Team_sport.objects.filter(team=team_b, sexo=sexo).exists():
            messages.error(request, "Algum campus não está cadastrado na modalidade!")
            return redirect('matches_register')

        if sport_id == 2 or sport_id == 1:
            volley_match = Volley_match.objects.create(status=0, event=event)
            volley_match.save()
            print("O esporte tem sets, blz? :)")
            if not Match.objects.filter(sport=sport_id, sexo=sexo, time_match=datetime, volley_match=volley_match, event=event).exists():
                match = Match.objects.create(sport=sport_id, sexo=sexo, time_match=datetime, volley_match=volley_match, event=event)
                Team_match.objects.create(match=match, team=team_a)
                Team_match.objects.create(match=match, team=team_b)
                messages.success(request, "Partida cadastrada com sucesso!")
            else:
                match = Match.objects.get(sport=sport_id, sexo=sexo, time_match=datetime, event=event)  
                messages.info(request, f"Essa partida já foi cadastrada! aidentificação dela é #{match.id}")
        else:  
            print("nao volei")  
            if not Match.objects.filter(sport=sport_id, sexo=sexo, time_match=datetime, event=event).exists():
                match = Match.objects.create(sport=sport_id, sexo=sexo, time_match=datetime, event=event)  
                Team_match.objects.create(match=match, team=team_a)
                Team_match.objects.create(match=match, team=team_b)
                messages.success(request, "Partida cadastrada com sucesso!")
            else:
                match = Match.objects.get(sport=sport_id, sexo=sexo, time_match=datetime, event=event)  
                messages.info(request, f"Essa partida já foi cadastrada! aidentificação dela é #{match.id}")
        match.save()
        return redirect('games')

@login_required
def manage_session(request):
    current_get_params = request.GET.urlencode()
    if request.method == "GET":
        context = {'users': User.objects.all()}
        if 'e' in request.GET and request.GET.get('e') != '':
            print("Né: ",request.GET.get('e'))
            user_session = User.objects.get(id=request.GET.get('e'))
            context['user_session'] = user_session
            context['sessions'] = UserSession.objects.filter(user=user_session)
        else:
            context['sessions'] = UserSession.objects.filter(user=request.user).select_related("session")

        return render(request, "manage_sessions.html", context)
    else:
        session_key = request.POST.get("session_key")
        if session_key and session_key != request.session.session_key:
            try:
                Session.objects.get(session_key=session_key).delete()
                UserSession.objects.filter(session__session_key=session_key).delete()
            except Session.DoesNotExist:
                pass
        if current_get_params:
            return redirect(f"{reverse('manage_sessions')}?{current_get_params}")
        else:
            return redirect("manage_sessions")

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.view_customuser', raise_exception=True)
def user_manage(request):
    team = Team.objects.all()
    context = {
        'team':team, 
        'events': Event.objects.all(), 
    }
    if not request.user.type in [0]:
        context['type_user'] = Users_types.choices[2:]
        context['users_all'] = User.objects.filter(event_user=request.user.event_user)
    elif 'e' in request.GET and request.GET['e'] != '':
        context['type_user'] = Users_types.choices
        context['users_all'] = User.objects.filter(event_user=Event.objects.get(id=request.GET['e']))
        context['select_event'] = request.GET['e']
    else:
        context['type_user'] = Users_types.choices
        context['users_all'] = User.objects.filter(event_user=None)
    
    if request.method == "GET":
        return render(request, 'settings/user_manage.html', context)
    else:
        print(request.POST, request.FILES)
        if 'user_id' in request.POST:
            user = get_object_or_404(User, id=request.POST.get('user_id'))
            print(user.username)
            print(user.password)
            if request.POST.get('name'): user.username = str(request.POST.get('name'))
            if request.POST.get('password'):
                senha = request.POST.get('password') 
                print("trocando: ", senha)
                user.set_password(senha)
            print("uaii")
            if int(request.POST.get('event')) != 0: user.event_user = Event.objects.get(id=request.POST.get('event'))
            else: user.event_user = None
            if request.POST.get('telephone'): user.telefone = request.POST.get('telephone')
            if request.POST.get('email'): user.email = str(request.POST.get('email'))
            if request.POST.get('active') == 'on': user.is_active = True
            else: user.is_active = False
            if request.POST.get('type'): 
                if int(request.POST.get('type')) == 2:
                    if request.POST.get('team'):
                        user.team = Team.objects.get(id=request.POST.get('team'))
                        user.type = request.POST.get('type')
                    else:
                        messages.info(request, f"O time/ou o tipo não foi alterado porque faltou informar o time.")
                else:
                    user.type = request.POST.get('type')
                    user.team = None
                
            if request.FILES.get('photo'):
                if user.photo: 
                    status = verificar_foto(str(user.photo))
                    if status:
                        user.photo.delete()
                user.photo = request.FILES.get('photo')
            user.save()
            print("Nova: ",user.password)
            messages.success(request, f"{user.username} do sistema atualizado com sucesso!")
        elif 'name' in request.POST:
            name = request.POST.get('name')
            if request.POST.get('event') and int(request.POST.get('event')) != 0: event = Event.objects.get(id=request.POST.get('event'))
            elif request.user.type == 1: event = request.user.event_user
            else: event = None
            type = request.POST.get('type')
            team = request.POST.get('team')
            email = request.POST.get('email')
            telephone = request.POST.get('telephone')
            password = request.POST.get('password')
            photo = request.FILES.get('photo')
            if int(type) == 2:
                if team: User.objects.create_user(username=name, password=password, photo=photo, type=type, team=Team.objects.get(id=team), email=email, telefone=telephone, event_user=event)
                elif request.user.team: User.objects.create_user(username=name, password=password, photo=photo, type=type, team=request.user.team, email=email, telefone=telephone, event_user=event)
                else: messages.error(request, "Você não informou o time associado ao usuário.")
            else:
                User.objects.create_user(username=name, password=password, photo=photo, type=type, email=email, telefone=telephone, event_user=event )
                messages.success(request, f"{name} cadastrado do sistema com sucesso!")
        elif 'user_delete' in request.POST:
            user_id = request.POST.get('user_delete')
            user_delete = User.objects.get(id=user_id)
            user_delete.delete()
            messages.info(request, f"{user_delete.username} removido do sistema com sucesso!")
        return redirect('user_manage')
    
@login_required(login_url="login")
@terms_accept_required
@permission_required('app.view_voluntary', raise_exception=True)
def voluntary_manage(request):
    user = User.objects.get(id=request.user.id)
    if user.is_staff:
        types = Type_service.choices
    else:
        types = Type_service.choices[:-1]
    if request.method == "GET":
        context = {
            'allowed': allowed_pages(user),
            'types': types,
            'users': User.objects.all(),
        }
        if not request.user.event_user: context['events'] = Event.objects.all()
        if 'e' in request.GET and request.GET['e'] != '' and 'q' in request.GET:
            context['voluntarys'] = Voluntary.objects.filter(name__icontains=request.GET['q'], event__id=request.GET['e'])
        elif 'e' in request.GET and request.GET['e'] != '':
            context['voluntarys'] = Voluntary.objects.filter(event__id=request.GET['e'])
            context['select_event'] = request.GET['e']
        elif 'q' in request.GET and request.GET['q'] != '':
            if request.user.event_user: context['voluntarys'] = Voluntary.objects.filter(name__icontains=request.GET['q'], event=request.user.event_user)
            else: context['voluntarys'] = Voluntary.objects.filter(name__icontains=request.GET['q'])
        elif user.type != 0:
            context['voluntarys'] = Voluntary.objects.filter(event=request.user.event_user)

        print(context)
        return render(request, 'voluntary/voluntary_manage.html', context)
    else:
        print(request.POST, "aa", request.FILES)
        get_param = request.GET.get('e') or request.POST.get('event') or ''
        redirect_url = f"{reverse('voluntary_manage')}?e={get_param}"
        if 'voluntary_delete' in request.POST:
            voluntary_id = request.POST.get('voluntary_delete')
            voluntary_delete = Voluntary.objects.get(id=voluntary_id)

            status = verificar_foto(str(voluntary_delete.photo))
            if status:
                voluntary_delete.photo.delete()
            voluntary_delete.delete()

            messages.success(request, f"{voluntary_delete.get_type_voluntary_display()} removido do sistema com sucesso!")

        elif 'voluntary_id' in request.POST:
            voluntary = get_object_or_404(Voluntary, id=request.POST.get("voluntary_id"))
            voluntary.name = request.POST.get('name')
            voluntary.registration = request.POST.get('registration')
            voluntary.type_voluntary = request.POST.get('type_voluntary')

            if request.user.is_staff:
                voluntary.admin = User.objects.get(id=request.POST.get('user'))
                voluntary.event = Event.objects.get(id=request.POST.get('event'))

            photo = request.FILES.get('photo')
            if photo:
                status = type_file(request, ['.png', '.jpg', '.jpeg'], photo,
                                   'A photo anexada não é do tipo png, jpg ou jpeg, considere converte-la em um desses tipos.')
                if status:
                    return redirect(redirect_url)

                if voluntary.photo:
                    status_photo = verificar_foto(str(voluntary.photo))
                    if status_photo:
                        voluntary.photo.delete()

                voluntary.photo = request.FILES.get('photo')

            voluntary.save()

        elif 'name' in request.POST:
            name = request.POST.get('name')
            registration = request.POST.get('registration')

            if not request.POST.get('type_voluntary'):
                messages.error(request, "Você não enviou todos os dados solicitados, confira e reenvie!")
                return redirect(redirect_url)

            type_voluntary = request.POST.get('type_voluntary')
            photo = request.FILES.get('photo')

            if photo:
                status = type_file(request, ['.png', '.jpg', '.jpeg'], photo,
                                   'A photo anexada não é do tipo png, jpg ou jpeg, considere converte-la em um desses tipos.')
                if status:
                    return redirect(redirect_url)

            if request.user.is_staff:
                event = Event.objects.get(id=request.POST.get('event'))
                admin = User.objects.get(id=request.POST.get('user'))
            else:
                admin = user
                event = request.user.event_user

            Voluntary.objects.create(
                type_voluntary=type_voluntary,
                name=name,
                registration=registration,
                admin=admin,
                photo=photo,
                event=event
            )
            messages.success(request, "Parabéns, você cadastrou mais um membro da comissão técnica!")
        return redirect(redirect_url)


@login_required(login_url="login")
@terms_accept_required
@permission_required('app.change_player_match', raise_exception=True)
@permission_required('app.add_player_match', raise_exception=True)
def players_in_teams(request, id):
        match = get_object_or_404(Match, id=id)
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
            print('O jogador não foi encontrado :(')
        except Exception as e:
            print(f'Um erro inesperado aconteceu: {str(e)}')
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
            print("IDs: ",player_id)
            for i in player_id:
                number = request.POST.get(f'number_{i}')
                if int(number) < 1:
                    messages.error(request, "Os números precisam ser maior que 1!")
                    return redirect('add_players_match', id)
                else:
                    print(request.POST.get(f'number_{i}'))              
                    print("ele ta continuando")
                    player = get_object_or_404(Player, id=i)
                    print(player)
                    player_match = Player_match.objects.create(match=team_match.match, team_match=team_match ,player=player, player_number=number)
                    print(player_match)
                    player_match.save()
                    print(player_match, "salvou")
        except ValueError:
            messages.error(request, "Você precisa informar os jogadores e seus respectivos números corretamente!")
            return redirect('add_players_match', id)

        return redirect('players_match', id)

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.add_banner', raise_exception=True)
def banner_register(request):
    if request.method == "GET":
        return render(request, 'settings/banner_register.html')
    else:
        name = request.POST.get('name')
        image = request.FILES.get('banner')
        if not name or not image:
            messages.eror(request, "Você precisa preencher todas as informações!")
            return redirect('banner_register')
        Banner.objects.create(name=name,image=image)
        return redirect('banner_register')

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.view_banner', raise_exception=True)
@permission_required('app.delete_banner', raise_exception=True)
@permission_required('app.change_banner', raise_exception=True)
def banner_manage(request):
    banner = Banner.objects.filter()
    if request.method == "GET":
        return render(request, 'settings/banner_manage.html',{'banner': banner})
    else:
        try:
            if 'banner_delete' in request.POST:
                banner_id = request.POST.get('banner_delete')
                banner_delete = Banner.objects.get(id=banner_id)
                banner_delete.delete()
                return redirect('banner_manage')
            if 'banner_update' in request.POST:
                banner_id = request.POST.get('banner_update')
                banner = Banner.objects.get(id=banner_id)
                if banner.status == 0: banner.status = 1
                elif banner.status == 1: 
                    banner.status = 0
                    if Banner.objects.filter(status=1):
                        banner2 = Banner.objects.filter(status=0)
                        for i in banner2:
                            i.status = 1
                            i.save()
                banner.save()
                return redirect('banner_manage')
        except Exception as e: messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return redirect('banner_manage')

@login_required(login_url="login")
def upload_document(request):
    try:
        termo = Terms_Use.objects.get(usuario=request.user)
    except Terms_Use.DoesNotExist:
        termo = Terms_Use(usuario=request.user)

    if request.method == 'POST':
        document = request.FILES.get('document')
        if document:
            termo.document = document
            if document: 
                status = type_file(request, ['.pdf','.png','.jpg','.jpeg'], document, 'O documento anexado precisa ser do tipo pdf, png, jpg ou jpeg.')
                if status: return redirect('upload_document')
            termo.save()
            return redirect('boss_data')

    return render(request, 'terms/terms_use_upload.html')


@login_required(login_url="login")
def boss_data(request):
    try:
        termo = Terms_Use.objects.get(usuario=request.user)
        if not termo.document:
            return redirect('upload_document')
    except Terms_Use.DoesNotExist:
        return redirect('upload_document')

    if request.method == 'POST':
        nome = request.POST.get('name')
        siape = request.POST.get('siape')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        photo = request.FILES.get('photo')

        if nome and siape and photo and email and phone:
            termo.name = nome
            termo.siape = siape
            termo.email = email
            termo.phone = phone
            if photo: 
                status = type_file(request, ['.png','.jpg','.jpeg'], photo, 'A photo anexada não é do tipo png, jpg ou jpeg, considere converte-la em um desses tipos.')
                if status: return redirect('boss_data')
            termo.photo = photo
            termo.save()
            return redirect('terms_use')
        else:
            messages.error(request, 'Você precisa preencher todas as informações!')
            return redirect('boss_data')

    return render(request, 'terms/terms_use_data.html')


@login_required(login_url="login")
def terms_use(request):
    try:
        termo = Terms_Use.objects.get(usuario=request.user)
        if not termo.document:
            return redirect('upload_document')
        if not (termo.name and termo.siape and termo.email and termo.phone and termo.photo):
            return redirect('boss_data')
    except Terms_Use.DoesNotExist:
        return redirect('upload_document')

    if request.method == 'POST':
        if request.POST.get('accept') == 'on':
            termo.accepted = True
            termo.accepted_at = timezone.now()
            termo.save()

            Voluntary.objects.create(
                name=termo.name,
                photo=termo.photo,
                campus=request.user.campus,
                registration=termo.siape,
                admin=request.user,
                type_voluntary=4
            )

            return redirect('Home')

    return render(request, 'terms/terms_use.html' , {'termo': termo})

@login_required(login_url="login")  
def settings(request):
    return render(request, 'settings.html')

@login_required(login_url="login")  
def settings_new(request):
    if request.POST:
        if 'banner_delete' in request.POST:
            banner = Banner.objects.get(id=request.POST.get('banner_delete'))
            banner.image.delete()
            banner.delete()
        elif 'attachments_delete' in request.POST:
            attachments = Attachments.objects.get(id=request.POST.get('attachments_delete'))
            attachments.file.delete()
            attachments.delete()
        elif 'statement_delete' in request.POST:
            statement = Statement.objects.get(id=request.POST.get('statement_delete'))
            statement.image.delete()
            statement.delete()
    context = {
        'banners': Banner.objects.all(),
        'attachments': Attachments.objects.all(),
        'statement': Statement.objects.all(),
    }
    return render(request, 'settings_new.html', context)

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.add_statement', raise_exception=True)
def statement_register(request):
    if request.method == "GET":
        return render(request, 'settings/statement_register.html')
    else:
        name = request.POST.get('name')
        image = request.FILES.get('image')
        if not name or not image:
            messages.eror(request, "Você precisa preencher todas as informações!")
            return redirect('statement_register')
        Statement.objects.create(name=name,image=image)
        return redirect('statement_manage')

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.view_statement', raise_exception=True)
@permission_required('app.delete_statement', raise_exception=True)
@permission_required('app.view_statement_user', raise_exception=True)
@permission_required('app.delete_statement_user', raise_exception=True)
def statement_manage(request):
    statement = Statement.objects.filter()
    statement_user = Statement_user.objects.all().order_by('statement')
    if request.method == "GET":
        return render(request, 'settings/statement_manage.html',{'statement': statement,'statement_user': statement_user})
    else:
        try:
            if 'statement_delete' in request.POST:
                statement_id = request.POST.get('statement_delete')
                statement_delete = Statement.objects.get(id=statement_id)
                statement_delete.delete()
                return redirect('statement_manage')
            elif 'statement_user_delete' in request.POST:
                statement_user_id = request.POST.get('statement_user_delete')
                statement_user_delete = Statement_user.objects.get(id=statement_user_id)
                statement_user_delete.delete()
                return redirect('statement_manage')
        except Exception as e: messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return redirect('statement_manage')

@login_required(login_url="login")
@permission_required('app.view_terms_use', raise_exception=True)
def chefe_manage(request):
    if request.method == "GET":
        terms = Terms_Use.objects.all()
        return render(request, 'settings/chefe_manage.html',{'terms': terms})
    else:
        try:
            if request.user.has_perm('app.delete_terms_use'):
                terms_delete = request.POST.get('terms_delete')
                term_del = Terms_Use.objects.get(id=terms_delete)
                term_del.delete()
                messages.success(request, "Excluido com sucesso!")
            else:
                messages.error(request, "Você não tem permissão para remover.")
            return redirect('chefe_manage')
        except Exception as e: messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return redirect('chefe_manage')

@login_required(login_url="login")
@permission_required('app.view_help', raise_exception=True)
def faq_manage(request):
    if request.method == "GET":
        help = Help.objects.all()
        return render(request, 'settings/faq_manage.html',{'help': help})
    else:
        try:
            if request.user.has_perm('app.delete_help'):
                faq_delete = request.POST.get('faq_delete')
                faq = Help.objects.get(id=faq_delete)
                faq.delete()
                messages.success(request, "Excluido com sucesso!")
            else:
                messages.error(request, "Você não tem permissão para remover.")
            return redirect('faq_manage')
        except Exception as e: messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return redirect('faq_manage')
    
@login_required(login_url="login")
@permission_required('app.view_attachments', raise_exception=True)
def anexo_manage(request):
    if request.method == "GET":
        atack = Attachments.objects.all().order_by('-id')
        return render(request, 'settings/anexo_manage.html',{'atack': atack})
    else: 
        try:
            if request.user.has_perm('app.delete_attachments'):
                atack_delete = request.POST.get('atack_delete')
                atack = Attachments.objects.get(id=atack_delete)
                atack.delete()
                messages.success(request, "Excluido com sucesso!")
            else:
                messages.error(request, "Você não tem permissão para remover.")
            return redirect('anexo_manage')
        except Exception as e: messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return redirect('anexo_manage')
    
@login_required(login_url="login")
@permission_required('app.view_settings_access', raise_exception=True)
def enrollment_manage(request):
    if request.method == "GET":
        date_list = Settings_access.objects.all().order_by('-id')
        return render(request, 'settings/enrollment_manage.html',{'date_list': date_list})
    else:
        try:
            if request.user.has_perm('app.delete_settings_access'):
                date_delete = request.POST.get('date_delete')
                settings_access = Settings_access.objects.get(id=date_delete)
                settings_access.delete()
                messages.success(request, "Excluido com sucesso!")
            else:
                messages.error(request, "Você não tem permissão para remover.")
            return redirect('enrollment_manage')
        except Exception as e: messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return redirect('enrollment_manage')
    
@login_required(login_url="login")
@permission_required('app.add_help', raise_exception=True)
def faq_register(request):
    if request.method == "GET":
        return render(request, 'settings/faq_register.html')
    else:
        try:
            title_faq = request.POST.get('title_faq')
            details_faq = request.POST.get('details_faq')
            Help.objects.create(title=title_faq, description=details_faq)
            messages.success(request, "Parabéns, foi cadastrado com sucesso!")
            return redirect('faq_manage')
        except Exception as e: messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return redirect('faq_manage')
    
@login_required(login_url="login") 
@permission_required('app.add_attachments', raise_exception=True)
def anexo_register(request):
    if request.method == "GET":
        return render(request, 'settings/anexo_register.html')
    else:
        try:
            title_atack = request.POST.get('title_atack')
            file_atack = request.FILES.get('file_atack')
            print(file_atack)
            print(request.POST, request.FILES)
            Attachments.objects.create(name=title_atack, user=request.user, file=file_atack)
            messages.success(request, "Parabéns, foi cadastrado com sucesso!")
            return redirect('anexo_manage')
        except Exception as e: messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return redirect('anexo_manage')
    
@login_required(login_url="login")
@permission_required('app.add_settings_access', raise_exception=True)
def enrollment_register(request):
    if request.method == "GET":
        return render(request, 'settings/enrollment_register.html')
    else:
        try:
            start = request.POST.get('date_start')
            end = request.POST.get('date_end')
            print(f'i: {start} - f: {end}')
            Settings_access.objects.create(start=start, end=end)
            messages.success(request, "Parabéns, foi cadastrado com sucesso!")
            return redirect('enrollment_manage')
        except Exception as e: messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return redirect('enrollment_manage')

@login_required(login_url="login")
@permission_required('app.add_attachments', raise_exception=True)
def scoreboard(request):  
    time_now = time.strftime("%H:%M:%S", time.localtime())
    if Match.objects.filter(status=1):
        match = Match.objects.get(status=1)
        team_matchs = Team_match.objects.filter(match=match)
        team_match_a = team_matchs[0]
        team_match_b = team_matchs[1]
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
    if request.method == "GET":
        context = {
            'point_types': Point_types.choices,
            'penalities_types': Type_penalties.choices,
            'match': match,
            'team_match_a': team_match_a,
            'team_match_b': team_match_b,
            'point_a': Point.objects.filter(team_match=team_match_a).count(),
            'point_b': Point.objects.filter(team_match=team_match_b).count(),
            'players_match_a': players_match_a,
            'players_match_b': players_match_b,
            'points': Point.objects.all(),
            'activity_types': Activity.choices,
            'occurrence': Occurrence.objects.order_by('-id')[:7],
            'seconds': seconds,
            'status': status,

        }
        print("context")
        return render(request, 'scoreboard.html', context)
    else:
        print(request.POST)
        if 'team-a' in request.POST:
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
        elif 'replacement_init' in request.POST:
            player_init = get_object_or_404(Player_match, id=request.POST.get("replacement_init"))
            player_init.activity = 0
            player_end = get_object_or_404(Player_match, id=request.POST.get("replacement_end"))
            player_end.activity = 1
            player_init.save(), player_end.save()
        elif 'penalties' in request.POST:
            
            pass
        elif 'team-a-point' in request.POST:
            if request.POST.get("team-a-point") == "+1" and request.POST.get("player-a-point"): 
                player = Player.objects.get(id=request.POST.get("player-a-point"))
                Point.objects.create(team_match=team_match_a, player=player)
            elif request.POST.get("team-a-point") == "+1": 
                Point.objects.create(team_match=team_match_a)
            elif request.POST.get("team-a-point") == "-1": 
                Point.objects.filter(team_match=team_match_a).last().delete()
        elif 'team-b-point' in request.POST:
            if request.POST.get("team-b-point") == "+1" and request.POST.get("player-b-point"):
                player = Player.objects.get(id=request.POST.get("player-b-point"))
                Point.objects.create(team_match=team_match_b, player=player)
            elif request.POST.get("team-b-point") == "+1": 
                Point.objects.create(team_match=team_match_b)
            elif request.POST.get("team-b-point") == "-1": 
                Point.objects.filter(team_match=team_match_b).last().delete()
        elif 'time_init' in request.POST:
            if match.time_start and match.time_end:
                print("O cronometro já finalizou!")
                return redirect('scoreboard')
            
            elif match.time_start:
                if Time_pause.objects.filter(match=match):
                    pause = Time_pause.objects.filter(match=match).last()
                    if pause.start_pause and not pause.end_pause:
                        pause.end_pause = time_now
                        pause.save()
                        return redirect('scoreboard')                
                    else:
                        pause_time = Time_pause.objects.create(start_pause=time_now,match=match)
                        pause_time.save()
                        return redirect('scoreboard')
                else:
                    pause_time = Time_pause.objects.create(start_pause=time_now,match=match)
                    pause_time.save()
                    print(pause_time)
                    return redirect('scoreboard')
            
            else:
                match.time_start = time_now
                match.save()
                return redirect('scoreboard')
                
        elif 'time_stop' in request.POST:
            if match.time_start and match.time_end:
                print("O cronometro foi finalizado!")
                return redirect('scoreboard')
            elif match.time_start:
                if Time_pause.objects.filter(match=match).last():
                    pause = Time_pause.objects.filter(match=match).last()
                    if pause.start_pause and not pause.end_pause:
                        pause.end_pause = time_now
                        pause.save()
                match.time_end = time_now
                match.save()
                return redirect('scoreboard')
            else:
                print("o cronometro precisa ser iniciado, para ser finalizado!")
                return redirect('scoreboard')
        return redirect('scoreboard')

def scoreboard_public(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
        if Volley_match.objects.filter(status=1):
            print("PARTIDA DE VOLEI")
            volley_match = Volley_match.objects.get(status=1)
            print(volley_match)
            match = Match.objects.filter(volley_match=volley_match.id).last()
            print(match)
            team_matchs = Team_match.objects.filter(match=match)
            print(team_matchs)
            team_match_a = team_matchs[0]
            team_match_b = team_matchs[1]
            if (match.volley_match.sets_team_a + match.volley_match.sets_team_b) % 2 == 0:
                print("par")
                teammatch1 = team_match_a
                teammatch2 = team_match_b
                sets_1 = match.volley_match.sets_team_a
                sets_2 = match.volley_match.sets_team_b
            else:
                print("impar")
                teammatch1 = team_match_b
                teammatch2 = team_match_a
                sets_1 = match.volley_match.sets_team_b
                sets_2 = match.volley_match.sets_team_a
            players_match_a = Player_match.objects.filter(team_match=teammatch1)
            players_match_b = Player_match.objects.filter(team_match=teammatch2)
            point_a = Point.objects.filter(team_match=teammatch1).count()
            point_b = Point.objects.filter(team_match=teammatch2).count()
            aces_a = Point.objects.filter(point_types=2,team_match=teammatch1).count()
            aces_b = Point.objects.filter(point_types=2,team_match=teammatch2).count()
            lack_a = Penalties.objects.filter(type_penalties=2,team_match=teammatch1).count()
            lack_b = Penalties.objects.filter(type_penalties=2,team_match=teammatch2).count()
            occurrence = Occurrence.objects.filter(match=match)
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
                'team_match_a':teammatch1,
                'team_match_b':teammatch2,
                'time_sets_a': sets_1,
                'sets_b': sets_2,
                'players_match_a':players_match_a,
                'players_match_b':players_match_b,
                'point_a':point_a,
                'point_b':point_b,
                'lack_a':lack_a,
                'lack_b':lack_b,
                'img_sexo':img_sexo,
                'sexo_color': sexo_color,
                'ball_sport': ball_sport,
                'aces_or_card': "Aces",
                'aces_or_card_a': aces_a,
                'aces_or_card_b': aces_b,
                'events': occurrence,
                'sexo_text':match.get_sexo_display(),
                'name_scoreboard': name_scoreboard,
                'event':event,
                

                
            }
            print(context)
            return render(request, 'public/scoreboard_public.html', context)
            
        elif Match.objects.filter(status=1):
            print("sport aleatorio")
            match = Match.objects.get(status=1)
            occurrence = Occurrence.objects.filter()
            team_matchs = Team_match.objects.filter(match=match)
            team_match_a = team_matchs[0]
            team_match_b = team_matchs[1]
            players_match_a = Player_match.objects.filter(team_match=team_match_a)
            players_match_b = Player_match.objects.filter(team_match=team_match_b)
            point_a = Point.objects.filter(team_match=team_match_a).count()
            point_b = Point.objects.filter(team_match=team_match_b).count()
            lack_a = Penalties.objects.filter(type_penalties=2,team_match=team_match_a).count()
            lack_b = Penalties.objects.filter(type_penalties=2,team_match=team_match_b).count()
            card_a = Penalties.objects.filter(type_penalties=0,team_match=team_match_a).count() + Penalties.objects.filter(type_penalties=1,team_match=team_match_a).count()
            card_b = Penalties.objects.filter(type_penalties=0,team_match=team_match_b).count() + Penalties.objects.filter(type_penalties=1,team_match=team_match_b).count()
            seconds, status = generate_timer(match)
            if match.sexo == 1: 
                img_sexo = static('images/icon-female.svg')
                sexo_color = '#ff32aa' 
            else: 
                img_sexo = static('images/icon-male.svg')
                sexo_color = '#3a7bd5'
            name_scoreboard = 'Tempo'
            if match.sport == 3:
                ball_sport = static('images/ball-of-handball.png')
            else:
                ball_sport = static('images/ball-of-futsal.png')
            context = {
                'match': match,
                'events': occurrence,
                'status': status,
                'seconds': seconds,
                'team_match_a':team_match_a,
                'team_match_b':team_match_b,
                'players_match_a':players_match_a,
                'players_match_b':players_match_b,
                'point_a':point_a,
                'point_b':point_b,
                'time_sets_a': "00:00",
                'lack_a':lack_a,
                'lack_b':lack_b,
                'img_sexo':img_sexo,
                'sexo_color': sexo_color,
                'ball_sport': ball_sport,
                'aces_or_card': "Cartões",
                'aces_or_card_a': card_a,
                'aces_or_card_b': card_b,
                'sexo_text':match.get_sexo_display(),
                'name_scoreboard': name_scoreboard,
                'event':event,
                
                
            }
            print(occurrence)
            print(context)
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
        url = request.get_host()
        print(url)

        # Gera o QR Code
        qr = qrcode.make(url)

        # Salva o QR em memória
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        buffer.seek(0)

        # Codifica em base64
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        if Volley_match.objects.filter(status=1):
            print("PARTIDA DE VOLEI")
            volley_match = Volley_match.objects.get(status=1)
            match = Match.objects.filter(volley_match=volley_match.id).last()
            team_matchs = Team_match.objects.filter(match=match)
            team_match_a = team_matchs[0]
            team_match_b = team_matchs[1]
            if (match.volley_match.sets_team_a + match.volley_match.sets_team_b) % 2 == 0:
                print("par")
                teammatch1 = team_match_a
                teammatch2 = team_match_b
                sets_1 = match.volley_match.sets_team_a
                sets_2 = match.volley_match.sets_team_b
            else:
                print("impar")
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
            print(point_a, point_b)
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
                'events': occurrence,
                'banner_score':banner_score,
                'banner_bol':banner_bol,
                'sexo_text':match.get_sexo_display(),
                'name_scoreboard': name_scoreboard,
                'qrcode': img_base64,
                'url': url,
                
                
            }
            print(context)
            return render(request, 'public/scoreboard_projector.html', context)
            
        elif Match.objects.filter(status=1):
            print("sport aleatorio")
            match = Match.objects.get(status=1)
            occurrence = Occurrence.objects.filter(match=match)
            team_matchs = Team_match.objects.filter(match=match)
            team_match_a = team_matchs[0]
            team_match_b = team_matchs[1]
            players_match_a = Player_match.objects.filter(team_match=team_match_a)
            players_match_b = Player_match.objects.filter(team_match=team_match_b)
            point_a = Point.objects.filter(team_match=team_match_a).count()
            point_b = Point.objects.filter(team_match=team_match_b).count()
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
                'lack_a':lack_a,
                'lack_b':lack_b,
                'ball_sport': ball_sport,
                'aces_a': 0,
                'aces_b': 0,
                'banner_score':banner_score,
                'banner_bol':banner_bol,
                'card_a': card_a,
                'card_b': card_b,
                'sexo_text':match.get_sexo_display(),
                'name_scoreboard': name_scoreboard,
                'qrcode': img_base64,
                'url': url,
                
                
            }
            return render(request, 'public/scoreboard_projector.html', context)
        else:
            return render(request, 'public/scoreboard_projector.html', {'qrcode': img_base64, 'url': url})
    except Exception as e:
        messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return render(request, 'public/scoreboard_projector.html')

@login_required(login_url="login")
@terms_accept_required
def generator_badge(request):
    try:
        if request.user.is_staff:
            team_sport = Team_sport.objects.all()
        else:
            team_sport = Team_sport.objects.filter(admin__id=request.user.id).order_by('team','sport','-sexo')     
        sport = Sport_types.choices
        user = User.objects.get(id=request.user.id)
        if request.method == "GET":
            context = {
                'team_sport': team_sport,
                'sport': sport,
                
            }
            return render(request, 'badge.html', context)
        else:
            if 'team-badge' in request.POST:
                team_badge = request.POST.get('team-badge')
                if team_badge.isdigit(): 
                    players = Player_team_sport.objects.filter(team_sport__id=team_badge)
                    team_sport_badge = Team_sport.objects.get(id=team_badge)
                    if len(players) == 0:
                        messages.error(request, "Não tem nenhum técnico cadastrado!")
                        return redirect('badge')
                    namebadge = f'{ team_sport_badge.get_sport_display() }-{ team_sport_badge.team.get_campus_display() }-jifs'
                    return generate_badges(players, user, '2',namebadge)
                else:
                    if team_badge == 'all_player':
                        players = Player_team_sport.objects.all()
                        if len(players) == 0:
                            messages.error(request, "Não tem nenhum atleta cadastrado!")
                            return redirect('badge')
                        namebadge = 'atletas-jifs'
                        return generate_badges(players, user, '2',namebadge)
                    elif team_badge == 'all_voluntary':
                        if user.is_staff: voluntary = Voluntary.objects.filter(type_voluntary=0)
                        else: voluntary = Voluntary.objects.filter(type_voluntary=0, admin=user)
                        if len(voluntary) == 0:
                            messages.error(request, "Não tem nenhum voluntário cadastrado!")
                            return redirect('badge')
                        print("a: ",voluntary)
                        namebadge = 'voluntarios-jifs'
                        return generate_badges(voluntary, user, '1',namebadge)
                    elif team_badge == 'all_organization':
                        if user.is_staff: voluntary = Voluntary.objects.filter(type_voluntary=2)
                        else: voluntary = Voluntary.objects.filter(type_voluntary=2, admin=user)
                        if len(voluntary) == 0:
                            messages.error(request, "Não tem nenhum membro do apoio cadastrado!")
                            return redirect('badge')
                        namebadge = 'apoio-jifs'
                        return generate_badges(voluntary, user, '4',namebadge)
                    elif team_badge == 'all_trainee':
                        if user.is_staff: voluntary = Voluntary.objects.filter(type_voluntary=3)
                        else: voluntary = Voluntary.objects.filter(type_voluntary=3, admin=user)
                        if len(voluntary) == 0:
                            messages.error(request, "Não tem nenhum estagiário cadastrado!")
                            return redirect('badge')
                        namebadge = 'estagiario-jifs'
                        return generate_badges(voluntary, user, '4',namebadge)
                    elif team_badge == 'all_technician':
                        if user.is_staff: voluntary = Voluntary.objects.filter(type_voluntary=1)
                        else: voluntary = Voluntary.objects.filter(type_voluntary=1, admin=user)
                        if len(voluntary) == 0:
                            messages.error(request, "Não tem nenhum técnico cadastrado!")
                            return redirect('badge')
                        namebadge = 'tecnico-modalidade-jifs'
                        return generate_badges(voluntary, user, '3',namebadge)
                    elif team_badge == 'all_head':
                        if user.is_staff: voluntary = Voluntary.objects.filter(type_voluntary=4)
                        else: voluntary = Voluntary.objects.filter(type_voluntary=4, admin=user)
                        if len(voluntary) == 0:
                            messages.error(request, "Não tem nenhum chefe de delegação cadastrado!")
                            return redirect('badge')
                        namebadge = 'chefe-delegacao-jifs'
                        return generate_badges(voluntary, user, '3',namebadge)
                    else:
                        for choice in Sport_types.choices:
                            if choice[1] == team_badge:
                                sport_value = choice[0]
                                break
                        players = Player_team_sport.objects.filter(team_sport__sport=sport_value)
                        if len(players) == 0:
                            messages.error(request, "Não tem nenhum atleta cadastrado!")
                            return redirect('badge')
                        namebadge = f'atletas-{team_badge}-jifs'
                        return generate_badges(players, user, '2',namebadge)
    except Exception as e:
        messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
    return redirect('badge')

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.add_certificate', raise_exception=True)
@permission_required('app.view_certificate', raise_exception=True)
def generator_certificate(request):
    try:
        user = User.objects.get(id=request.user.id)
        if request.user.is_staff:
            team_sport = Team_sport.objects.all()
        else:
            team_sport = Team_sport.objects.filter(admin__id=request.user.id).order_by('team','sport','-sexo')
        certificate = Certificate.objects.filter(user=request.user.id)
        sport = Sport_types.choices
        if request.method == "GET":
            context = {
                'team_sport': team_sport,
                'sport': sport,
                'certificate': certificate,
                
            }
            return render(request, 'certificate.html', context)
        else:
            if 'certificate_delete' in request.POST:
                certificate_delete = request.POST.get('certificate_delete')
                certificate = Certificate.objects.get(id=certificate_delete)
                certificate.file.delete()
                certificate.delete()
                return redirect('certificate')
            elif 'certificate_all_delete' in request.POST:
                certificate = Certificate.objects.all()
                for i in certificate:
                    i.file.delete()
                    i.delete()
                return redirect('certificate')
            elif 'team-certificate' in request.POST:
                team_certificate = request.POST.get('team-certificate')
                if team_certificate.isdigit(): 
                    team_sport = get_object_or_404(Team_sport, id=team_certificate) 
                    players = Player_team_sport.objects.filter(team_sport=team_sport)
                    generate_certificates(players, user, '2')
                else:
                    if team_certificate == 'all_player':
                        players = Player_team_sport.objects.all()
                        generate_certificates(players, user, 0)
                    elif team_certificate == 'all_voluntary':
                        voluntary = Voluntary.objects.filter(type_voluntary=0, admin=user)
                        print("a: ",voluntary)
                        generate_certificates(voluntary, user, 1)
                    elif team_certificate == 'all_organization':
                        voluntary = Voluntary.objects.filter(type_voluntary=1, admin=user)
                        generate_certificates(voluntary, user, 1)
                    elif team_certificate == 'all_technician':
                        voluntary = Voluntary.objects.filter(type_voluntary=2, admin=user)
                        generate_certificates(voluntary, user, 1)
                    else:
                        for choice in Sport_types.choices:
                            if choice[1] == team_certificate:
                                sport_value = choice[0]
                                break
                        players = Player_team_sport.objects.filter(team_sport__sport=sport_value)
                return redirect('certificate')
            return redirect('certificate')
    except Exception as e:
        messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
    return redirect('certificate')

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.data', raise_exception=True)
def generator_data(request):
    try:
        user = User.objects.get(id=request.user.id)
        if request.method == "GET":
            if request.user.is_staff: 
                team_sport = Team_sport.objects.filter(players__isnull=False).distinct().order_by('team__campus','sport','-sexo')
            else: 
                team_sport = Team_sport.objects.all().filter(players__isnull=False, admin=user).order_by('team__campus','sport','-sexo')
            sports = [i.sport for i in team_sport]
            context = {
                'sexo': Sexo_types.choices,
                'team_sport': team_sport,
                'campus': Campus_types.choices,
                'sports': sports,
                'sports_general': Sport_types.choices,
                
            }
            
            print(context)
            return render(request, 'data.html', context)
        else:
            cont = {
                'now': timezone.now(),
                'user': user,
                'logo_ifs': request.build_absolute_uri('/static/images/logo-jiifs-2025.jpg'),
                'logo_morea': request.build_absolute_uri('/static/images/logo_ifs.png')
            }
            if 'all_data' in request.POST:
                name_html = 'data-general'
                name_pdf = 'dados_gerais'
                cont['qnt_campus'] = 10
                
                qnt_players = Player.objects.all().count()
                qnt_players_fem = Player.objects.filter(sexo=1).count()
                qnt_players_masc = Player.objects.filter(sexo=0).count()
                cont['qnt_players'] = qnt_players
                cont['qnt_players_fem'] = qnt_players_fem
                cont['qnt_players_masc'] = qnt_players_masc
                cont['qnt_teams'] = Team_sport.objects.all().count()
                cont['qnt_voluntary_0'] = Voluntary.objects.filter(type_voluntary=0).count()
                cont['qnt_voluntary_1'] = Voluntary.objects.filter(type_voluntary=1).count()
                cont['qnt_voluntary_2'] = Voluntary.objects.filter(type_voluntary=2).count()
                cont['qnt_voluntary_3'] = Voluntary.objects.filter(type_voluntary=3).count()
                cont['qnt_voluntary_4'] = Voluntary.objects.filter(type_voluntary=4).count()
                for i in range(10):
                    cont[f'qnt_campus_{i}'] = Player.objects.filter(campus=i).count()

                cont['campi'] = []
                campi = Campus_types.choices
                campi.pop()
                cont['porcent_fem'] = (qnt_players_fem * 100) / qnt_players
                cont['porcent_masc'] = (qnt_players_masc * 100) / qnt_players
                for i in campi: 
                    campus_name = Campus_types(i[0]).label
                    players_total = Player.objects.filter(campus=i[0]).count()
                    players_fem = Player.objects.filter(campus=i[0], sexo=1).count()
                    players_masc = Player.objects.filter(campus=i[0], sexo=0).count()
                    qnt_voluntary_0 = Voluntary.objects.filter(type_voluntary=0, campus=i[0]).count()
                    qnt_voluntary_1 = Voluntary.objects.filter(type_voluntary=1, campus=i[0]).count()
                    qnt_voluntary_2 = Voluntary.objects.filter(type_voluntary=2, campus=i[0]).count()
                    qnt_voluntary_3 = Voluntary.objects.filter(type_voluntary=3, campus=i[0]).count()
                    qnt_voluntary_4 = Voluntary.objects.filter(type_voluntary=4, campus=i[0]).count()
                    cont['campi'].append([campus_name, players_total, players_fem, players_masc,qnt_voluntary_0,qnt_voluntary_1,qnt_voluntary_2,qnt_voluntary_3,qnt_voluntary_4])
        
            elif 'enrollment' in request.POST:
                name_html = 'data-base-enrollment'
                name_pdf = 'relatório de inscrições'
                teams = Team_sport.objects.prefetch_related('players').all().order_by('team__campus','sport','-sexo')
                if len(teams) == 0:
                    messages.error(request, "Não há equipes em modalidades ou atletas cadastrados.")
                    return redirect('data')
                cont['teams'] = teams

            elif 'all_campus' in request.POST:
                name_html = 'data-base-campus'
                name_pdf = 'dados_campus'
                if user.is_staff: teams = Team_sport.objects.prefetch_related('players').all().order_by('team__campus','sport','-sexo')
                else: teams = Team_sport.objects.prefetch_related('players').filter(admin=user).order_by('team__campus','sport','-sexo')
                if len(teams) == 0:
                    messages.error(request, "Você não está cadastrado em alguma modalidade ou não há atletas cadastrados.")
                    return redirect('data')
                cont['teams'] = teams
                cont['infor'] = "campus x modalidade x atletas"

            elif 'all_match' in request.POST:
                name_html = 'data-base-match'
                name_pdf = 'partidas_jifs'
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
                if len(matchs) == 0:
                    messages.error(request, "Não há nenhuma partida programada.")
                    return redirect('data')
                cont['context'] = context

            elif 'all_eqp' in request.POST:
                name_html = 'data-base-eqp'
                name_pdf = 'dados_equipe_jifs'
                cont['infor'] = "comissão técnica do jifs 2025"
                if user.is_staff: voluntary = Voluntary.objects.all().order_by('campus','-type_voluntary')
                else: voluntary = Voluntary.objects.filter(admin=user).order_by('campus','-type_voluntary')
                if len(voluntary) == 0:
                    messages.error(request, "Não há voluntários, técnicos, atletas ou chefe de delegação cadastrados.")
                    return redirect('data')
                cont['team'] = voluntary

            elif 'all_players' in request.POST:
                name_html = 'data-base'
                name_pdf = 'dados_atletas'
                cont['infor'] = "atletas"
                if user.is_staff: players = Player.objects.all().order_by('campus','-sexo')
                else: players = Player.objects.filter(admin=user).order_by('campus','-sexo')
                if len(players) == 0:
                    messages.error(request, "Não há atletas cadastrados.")
                    return redirect('data')  
                cont['players'] = players

            elif 'all_players_fem' in request.POST:
                name_html = 'data-base'
                name_pdf = 'dados_atletas'
                if user.is_staff: players = Player.objects.filter(sexo=1).order_by('campus','-sexo')
                else: players = Player.objects.filter(sexo=1, admin=user).order_by('campus','-sexo')
                if len(players) == 0:
                    messages.error(request, "Não há atletas do sexo feminino cadastrados.")
                    return redirect('data')
                cont['players'] = players
                cont['infor'] = "atletas do sexo feminino"
                cont['type'] = True

            elif 'all_players_masc' in request.POST:
                name_html = 'data-base'
                name_pdf = 'dados_atletas'
                if user.is_staff: players = Player.objects.filter(sexo=0).order_by('campus','-sexo')
                else: players = Player.objects.filter(sexo=0, admin=user).order_by('campus','-sexo')
                if len(players) == 0:
                    messages.error(request, "Não há atletas do sexo masculino cadastrados.")
                    return redirect('data')
                cont['players'] = players
                cont['infor'] = "atletas do sexo masculino"
                cont['type'] = True

            elif 'campus_in' in request.POST and user.is_staff:
                campus_id = request.POST.get('campus_in')
                campus_name = Campus_types(int(campus_id)).label.lower()

                name_html = 'data-base-campus-individual'
                name_pdf = f'atletas_{campus_name}'
                players = Player_team_sport.objects.filter(team_sport__team__campus=campus_id).order_by('player__campus','-player__sexo')
                if len(players) == 0:
                    messages.error(request, "Não há atletas cadastrados.")
                    return redirect('data')
                cont['players'] = players
                cont['infor'] = "atletas"
                cont['campus'] = f'{campus_name}'

            elif 'all_players_sport' in request.POST:
                name_pdf = 'dados_atletas'
                data = request.POST.get('all_players_sport')
                name_sport = Sport_types(int(data)).label
                if user.is_staff:
                    print("uaii")
                    name_html = 'data-base-campus'
                    teams = Team_sport.objects.prefetch_related('players').filter(sport=data).order_by('team__campus','sport','-sexo')
                    if len(teams) == 0:
                        messages.error(request, "Não há equipes em modalidades ou atletas cadastrados.")
                        return redirect('data')
                    cont['teams'] = teams
                    cont['infor'] = f"atletas da modalidade {name_sport}"
                else:
                    name_html = 'data-base-campus'
                    teams = Team_sport.objects.prefetch_related('players').filter(sport=data, admin=user).order_by('team__campus','sport','-sexo')
                    if len(teams) == 0:
                        messages.error(request, "Não há equipes em modalidades ou atletas cadastrados.")
                        return redirect('data')
                    cont['teams'] = teams
                    cont['infor'] = f"atletas da modalidade {name_sport}"
                    #players = Player_team_sport.objects.filter(team_sport__sport=data, team_sport__admin=user)
                    #if len(players) == 0:
                    #    messages.error(request, f'Não há atletas cadastrados no {name_sport}.')
                    #    return redirect('data')
                    #cont['players'] = players
                    #if players:
                    #    cont['infor'] = f'atletas da modalidade {players[0].team_sport.get_sport_display()}'
            html_string = render_to_string(f'generator/{name_html}.html', cont)

            response = HttpResponse(content_type='application/pdf')
            # response['Content-Disposition'] = f'inline; filename="{name_pdf}.pdf"'
            response['Content-Disposition'] = f'attachment; filename="{name_pdf}.pdf"'

            HTML(string=html_string).write_pdf(response)

            return response
    except Exception as e:
        messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
    return redirect('data')

@time_restriction("team_manage")
@login_required(login_url="login")
@terms_accept_required
@permission_required('app.add_team_sport', raise_exception=True)
def register_team(request, event_id):
    sports = Event_sport.objects.filter(event__id=event_id)
    context = {'sports': sports, 'event_id': event_id}
    if request.method == 'GET':
        if request.user.type in [0, 1]: 
            context['teams'] = Team.objects.all().order_by('-id')
            context['events'] = Event.objects.all().order_by('-id')
            return render(request, 'guiate/team_register_admin.html', context)
        else:
            if len(Team_sport.objects.filter(admin=request.user)) == 0: context['button_return_manage'] = True 
            return render(request, 'guiate/team_register.html', context)
    else:
        if 'add-team' in request.POST:
            print("Água")
        
        return redirect('guiate_register_team', event_id)
    
@time_restriction("team_manage")
@login_required(login_url="login")
@terms_accept_required  
@permission_required('app.add_team_sport', raise_exception=True)
def team_sexo(request, sport_name, event_id):
    sport_team = {label: value for value, label in Sport_types.choices}
    sport = Event_sport.objects.get(sport=sport_team[sport_name])
    event = Event.objects.get(id=event_id)
    context = {'sport': sport,'event_id':event_id}
    if request.method == 'GET':
        return render(request, 'guiate/team_sexo.html', context)
    else:
        print("cirand tema")
        print(request.POST)
        sexo = request.POST.get('sexo')
        if request.user.team and request.user.event_user:
            print("entrando")
            if not Team_sport.objects.filter(team=request.user.team, sport=sport, sexo=int(sexo), event=event).exists():
                team_sport = Team_sport.objects.create(team=request.user.team, sport=sport, sexo=int(sexo), admin=User.objects.get(id=request.user.id), event=event)
                messages.success(request, "O seu campus foi cadastrado em uma nova modalidade, parabéns!")
                print("O seu campus foi cadastrado em uma nova modalidade, parabéns!")
            else:
                team_sport = Team_sport.objects.get(team=request.user.team, sport=sport, sexo=int(sexo), event=event)
                messages.info(request, "O seu campus já está cadastrado nessa modalidade, adicione atletas!")
                print("O seu campus já está cadastrado nessa modalidade, adicione atletas!")
                if Player_team_sport.objects.filter(team_sport=team_sport).exists():
                    return redirect('guiate_players_list', team_sport.team.name, team_sport.get_sexo_display(),team_sport.sport.get_sport_display())
            return redirect('guiate_players_team', team_sport.team.name, team_sport.get_sexo_display(),team_sport.sport.get_sport_display(), team_sport.event.id)
        else:
            messages.info(request, "Observamos que você não tem um time associado os seu usuário ou um evento impossibilitando a ação.")
            return redirect('guiate_register_team', event_id)   

@time_restriction("team_manage")
@login_required(login_url="login")
@terms_accept_required
@permission_required('app.add_player', raise_exception=True)
@permission_required('app.add_player_team_sport', raise_exception=True)
def players_team(request, team_name, team_sexo, sport_name, event_id):
    user = User.objects.get(id=request.user.id)
    sport_team = {label: value for value, label in Sport_types.choices}
    sexo_team = {label: value for value, label in Sexo_types.choices}
    sport = Event_sport.objects.get(sport=sport_team[sport_name], event=request.user.event_user)
    sexo = sexo_team[team_sexo]
    team_sport = Team_sport.objects.get(team__name=team_name, sexo=sexo, sport=sport, event__id=event_id)
    players = Player.objects.all()
    events = Event.objects.all()
    if request.method == 'GET':
        if not players: messages.info(request, "Não tem nenhum jogador cadastrado no sistema!")
        return render(request, 'guiate/player_register_team.html', {'players': players,'team_sport': team_sport,'events': events}) 
    else:
        print(request.POST)
        if 'qe' in request.POST: 
            qe = request.POST.get('qe')
            if request.user.type == 0 or request.user.type == 1:
                if qe.isdigit(): player_filter = Player.objects.filter(registration=int(qe), event__id=event_id)
                else: player_filter = Player.objects.filter(name__icontains=qe, event__id=event_id)
            else:
                if qe.isdigit(): player_filter = Player.objects.filter(registration=int(qe), event__id=event_id, admin=user)
                else: player_filter = Player.objects.filter(name__icontains=qe, event__id=event_id, admin=user)
            if len(player_filter) > 1:
                messages.error(request, f"{len(player_filter)} atletas foram encontrados, seja mais preciso, você pode buscar pelo nome e pela matrícula!")
            elif len(player_filter) == 0:
                messages.error(request, "O atleta não foi encontrado!")
                return redirect('guiate_players_team', team_sport.team.name, team_sport.get_sexo_display(), team_sport.sport.get_sport_display(), team_sport.event.id)
            else:
                player = Player.objects.get(id=player_filter.first().id)
                if not Player_team_sport.objects.filter(player=player, team_sport=team_sport):          
                    Player_team_sport.objects.create(player=player, team_sport=team_sport)        
                    messages.success(request, f"O atleta {player.name} foi cadastrado na modalidade com sucesso!")
                    return redirect('guiate_players_list', team_sport.team.name, team_sport.get_sexo_display(),team_sport.sport.get_sport_display())
                else:
                    messages.info(request, f"O atleta {player.name} já está cadastrado, tá?!")
                    return redirect('guiate_players_list', team_sport.team.name, team_sport.get_sexo_display(),team_sport.sport.get_sport_display())
        elif 'name' in request.POST:
            number_players = len(Player_team_sport.objects.filter(team_sport=team_sport))
            if number_players >= team_sport.sport.max_sport:
                messages.error(request, "O seu campus atingiu o limite de atletas nessa modalidade!")
                print("O seu campus atingiu o limite de atletas nessa modalidade!")
                return redirect('guiate_players_list', team_sport.team.name, team_sport.get_sexo_display(),team_sport.sport.get_sport_display()) 
            name = request.POST.get('name')
            date_nasc = datetime.strptime(request.POST.get('date'), "%Y-%m-%d")
            date_today = date.today()
            if (date_today.year - date_nasc.year) > 19:
                messages.error(request, "O atleta não pode ser cadastrado por conta da idade :(")
                print("O atleta não pode ser cadastrado por conta da idade :(")
                return redirect('guiate_players_team', team_sport.team.name, team_sport.get_sexo_display(),team_sport.sport.get_sport_display(), team_sport.event.id)
            registration = request.POST.get('registration')
            cpf = request.POST.get('cpf')
            cpf = cpf.replace("-","").replace(".","")
            photo = request.FILES.get('photo')
            if request.POST.get('event') and request.user.type == 0: event = Event.objects.get(id=request.POST.get('event'))
            else: event = Event.objects.get(id=request.user.event_user.id)
            if photo: 
                print(photo)
                status = type_file(request, ['.png','.jpg','.jpeg'], photo, 'A photo anexada não é do tipo png, jpg ou jpeg, considere converte-la em um desses tipos.')
                if status: return redirect('guiate_players_team', team_sport.team.name, team_sport.get_sexo_display(),team_sport.sport.get_sport_display(), team_sport.event.id)
            bulletin = request.FILES.get('bulletin')
            if bulletin: 
                status = type_file(request, ['.pdf'], bulletin, 'O boletim escolar anexado não é do tipo pdf, que é o tipo aceito.')
                if status: return redirect('guiate_players_team', team_sport.team.name, team_sport.get_sexo_display(),team_sport.sport.get_sport_display(), team_sport.event.id)
            rg = request.FILES.get('rg')
            if rg: 
                status = type_file(request, ['.png','.jpg','.jpeg','.pdf','docx'], rg, 'O RG anexado não é faz parte dos tipos aceito, os tipos são png, jpg, jpeg, pdf ou docs.')
                if status: return redirect('guiate_players_team', team_sport.team.name, team_sport.get_sexo_display(),team_sport.sport.get_sport_display(), team_sport.event.id)
            if team_sport.sport.sport == 2:
                print("espote 2")
                sexo = request.POST.get('sexo')
                if not Player.objects.filter(name=name, sexo=sexo, cpf=cpf, date_nasc=date_nasc, registration=registration, admin=user, event=event).exists():
                    player = Player.objects.create(name=name, sexo=sexo, cpf=cpf, date_nasc=date_nasc, bulletin=bulletin, registration=registration, rg=rg, photo=photo, admin=user, event=event)
                else:
                    player = Player.objects.get(name=name, sexo=sexo, cpf=cpf, date_nasc=date_nasc, registration=registration, admin=user, event=event)
            else:
                print("aleratorio")
                if not Player.objects.filter(name=name, sexo=team_sport.sexo, cpf=cpf, date_nasc=date_nasc, registration=registration, admin=user, event=event).exists():
                    player = Player.objects.create(name=name, sexo=team_sport.sexo, rg=rg, cpf=cpf, date_nasc=date_nasc, bulletin=bulletin, registration=registration, photo=photo, admin=user, event=event)
                    print("criando novo atleta", team_sport.sexo, team_sport.get_sexo_display())
                else:
                    player = Player.objects.get(name=name, sexo=team_sport.sexo, cpf=cpf, date_nasc=date_nasc, registration=registration, admin=user, event=event)
            if not Player_team_sport.objects.filter(player=player, team_sport=team_sport):          
                Player_team_sport.objects.create(player=player, team_sport=team_sport)        
                messages.success(request, "O jogador foi cadastrado no sistema com sucesso!")
                print("O jogador foi cadastrado no sistema com sucesso!")
            else:
                messages.info(request, "O jogador já está cadastrado nessa modalidade, tá?!")
            return redirect('guiate_players_list', team_sport.team.name, team_sport.get_sexo_display(),team_sport.sport.get_sport_display())
        return redirect('guiate_players_team', team_sport.team.name, team_sport.get_sexo_display(),team_sport.sport.get_sport_display(), team_sport.event.id)

@login_required(login_url="login")
@terms_accept_required
@permission_required('app.view_player', raise_exception=True)
@permission_required('app.view_player_team_sport', raise_exception=True)
def players_list(request, team_name, team_sexo, sport_name):
        sport_team = {label: value for value, label in Sport_types.choices}
        sexo_team = {label: value for value, label in Sexo_types.choices}
        sport = Event_sport.objects.get(sport=sport_team[sport_name], event=request.user.event_user)
        sexo = sexo_team[team_sexo]
        team_sport = Team_sport.objects.get(team__name=team_name, sexo=sexo, sport=sport)
        players = Player_team_sport.objects.filter(team_sport=team_sport)
        if request.method == "GET":
            return render(request, 'guiate/players_list.html', {'team_sport':team_sport, 'players':players, 'allowed': allowed_pages(request.user)})
        else:
            if 'player_delete' in request.POST:
                if request.user.has_perm('app.delete_player_team_sport') and request.user.has_perm('app.delete_player'):
                    player_id = request.POST.get("player_delete")
                    player = Player_team_sport.objects.get(id=player_id)
                    player.delete()
                    print("eupa")
                    if not Player_team_sport.objects.filter(id=player_id).exists():
                        print("eupaESSS")
                        player_table = Player.objects.get(id=player.player.id)
                        status = verificar_foto(str(player_table.photo))
                        if status:
                            player_table.photo.delete()
                        player_table.bulletin.delete()
                        player_table.rg.delete()
                        player_table.delete()
                    messages.success(request, "O jogador foi removido com sucesso!")
                    print("O jogador foi cadastrado no sistema com sucesso!")
                else:
                    messages.error(request, "Você não tem permissão para remover.")

                return redirect('guiate_players_list', team_sport.team.name, team_sport.get_sexo_display(),team_sport.sport.get_sport_display())
            if 'Cancelar' in request.POST:
                if Player_team_sport.objects.filter(team_sport=team_sport).exists():
                    player_t_s = Player_team_sport.objects.filter(team_sport=team_sport)
                    for i in player_t_s:
                        i.delete()
                team_sport.delete()
                if not Team_sport.objects.filter(team=team_sport.team.id):
                    Team.objects.get(id=team_sport.team.id).delete()
                return redirect('team_manage')

@time_restriction("team_manage")
@login_required(login_url="login")
@terms_accept_required
@permission_required('app.change_player', raise_exception=True)
def player_list_edit(request, team_name, id, team_sexo, sport_name):
    try:
        campus = Campus_types.choices
        player = get_object_or_404(Player, id=id)
        sport_team = {label: value for value, label in Sport_types.choices}
        sexo_team = {label: value for value, label in Sexo_types.choices}
        sport = sport_team[sport_name]
        sexo = sexo_team[team_sexo]
        team_sport = Team_sport.objects.get(team__name=team_name, sexo=sexo, sport=sport)
        if request.method == 'GET':
            return render(request, 'guiate/player_list_edit.html', {'player': player, 'campus': campus, 'team_sport': team_sport})            
        else:
            print(request.FILES)
            player.name = request.POST.get('name')
            player.sexo = request.POST.get('sexo')
            player.registration = request.POST.get('registration')
            player.cpf = request.POST.get('cpf')
            photo = request.FILES.get('photo')
            print("verifica:")
            if photo:
                print("photo")
                status = type_file(request, ['.png','.jpg','.jpeg'], photo, 'A photo anexada não é do tipo png, jpg ou jpeg, considere converte-la em um desses tipos.')
                if not status:
                    print("status")
                    status_photo = verificar_foto(str(player.photo))
                    if status_photo:
                        player.photo.delete()
                    player.photo = photo
            campus_id = request.POST.get('campus')
            if campus_id:
                player.campus = campus_id
            player.save()
            messages.success(request, "Os dados do atleta foram atualizados com sucesso!")
            return redirect('guiate_players_list', team_sport.team.name, team_sport.get_sexo_display(),team_sport.sport.get_sport_display())
    except Exception as e: messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
    return redirect('Home')

@login_required(login_url="login")
@terms_accept_required 
def dashboard(request):
    return render(request, 'guiate/dashboard.html', {'players': Player_team_sport.objects.all()})

def allowed_pages(user):
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(brasilia_tz)
    
    config = Settings_access.objects.order_by('-id').first()

    if config:
        if config.start.tzinfo is None:
            config.start = brasilia_tz.localize(config.start)
        if config.end.tzinfo is None:
            config.end = brasilia_tz.localize(config.end)
    
    if not config or (config.start <= now <= config.end) or user.is_staff:  
        allowed = True
    else:
        allowed = False
    return allowed

def verificar_foto(url_name):
    print("url: ", url_name)
    list = ['person.png','team.png']
    url = url_name.split('/')
    delete_photo = url[len(url) - 1]
    if delete_photo in list:
        return False
    return True

def type_file(request, rest, file, text):
    ext = os.path.splitext(file.name)[1].lower().strip()
    if ext not in rest:
        messages.error(request, text)
        return True
    return False

