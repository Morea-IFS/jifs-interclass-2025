"""Views de gerenciamento de times e modalidades."""

import logging

from datetime import datetime as dt_module

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.db import IntegrityError
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from weasyprint import HTML

from app.decorators import time_restriction, terms_accept_required
from app.helpers import (
    SEXO_NAMES,
    acesso_evento,
    acesso_team,
    acesso_team_sport,
    calcular_idade,
    check_gender_compatibility,
    player_queryset_for_team,
    type_file,
    verificar_foto,
)
from app.models import (
    Campus_types,
    Event,
    Event_sport,
    Event_unit,
    Player,
    Player_team_sport,
    Sexo_types,
    Sport_types,
    Team,
    Team_sport,
    Voluntary,
)
from app.services.pdf import build_pdf_context, get_logo_event_type

logger = logging.getLogger(__name__)
User = get_user_model()


@time_restriction()
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
            context['event'] = Event.objects.get(id=e)

        elif e and t:
            context['teams'] = Team.objects.filter(event__id=e)
            context['events_sport'] = Event_sport.objects.filter(event__id=e)
            context['team_sports'] = Team_sport.objects.filter(team__id=t, team__event__id=e)
            context['team'] = Team.objects.get(id=t)
            context['voluntarys'] = Voluntary.objects.filter(event__id=e, type_voluntary=1)
            context['select_event'] = e
            context['event'] = Event.objects.get(id=e)

        elif e:
            context['teams'] = Team.objects.filter(event__id=e)
            context['events_sport'] = Event_sport.objects.filter(event__id=e)
            context['select_event'] = e
            context['event'] = Event.objects.get(id=e)

        elif t and request.user.type == 1:
            context['teams'] = Team.objects.filter(event__id=request.user.event_user.id)
            context['events_sport'] = Event_sport.objects.filter(event__id=request.user.event_user.id)
            context['team'] = Team.objects.get(id=t)
            context['team_sports'] = Team_sport.objects.filter(team__id=t)
            context['users'] = User.objects.filter(event_user=request.user.event_user)

        elif request.user.type == 1:
            context['teams'] = Team.objects.filter(event__id=request.user.event_user.id)
            context['events_sport'] = Event_sport.objects.filter(event__id=request.user.event_user.id)

        elif request.user.type == 2:
            context['team'] = Team.objects.get(id=request.user.team.id)
            context['team_sports'] = Team_sport.objects.filter(team__id=request.user.team.id)
            context['events_sport'] = Event_sport.objects.filter(event__id=request.user.event_user.id)

        return render(request, 'team/team_manage.html', context)

    else:
        try:
            if 'add-team' in request.POST:
                name = request.POST.get("name")
                color = request.POST.get("color")
                description = request.POST.get("description")
                photo = request.FILES.get("photo")
                event = Event.objects.get(id=request.POST.get("add-team"))
                if not acesso_evento(request.user, event):
                    messages.error(request, "Você não tem permissão para cadastrar times neste evento.")
                    return redirect('team_manage')
                if not name or not photo or not event:
                    messages.error(request, "Você precisa cadastrar todos os dados obrigatórios.")
                else:
                    team = Team.objects.create(name=name, description=description, photo=photo, event=event)
                    if color:
                        team.color = str(color)
                    team.save()
            elif 'add-team-sport' in request.POST:
                team = Team.objects.get(id=request.POST.get("add-team-sport"))
                if not acesso_team(request.user, team):
                    messages.error(request, "Você não tem permissão para modificar este time.")
                    return redirect('team_manage')
                sport = Event_sport.objects.get(id=request.POST.get("sport_adm_id"))
                sexo = int(request.POST.get("sexo_adm_id"))
                if not Team_sport.objects.filter(team=team, sport=sport, sexo=sexo, event=sport.event):
                    if sexo == 0 and not sport.masc or sexo == 1 and not sport.fem or sexo == 2 and not sport.mist:
                        messages.error(request, "O esporte escolhido não está disponível para este sexo. Em caso de dúvidas, consulte o regulamento.")
                    else:
                        team_sport = Team_sport.objects.create(team=team, sport=sport, sexo=sexo, event=sport.event)
                        if request.POST.get("technitian"):
                            team_sport.technitian = Voluntary.objects.get(id=request.POST.get("technitian"))
                        team_sport.save()
                        messages.success(request, "Esporte cadastrado com sucesso, adicione atletas.")
                else:
                    messages.info(request, "O esporte já existe, adicione atletas.")
            elif 'edit-team' in request.POST:
                team = Team.objects.get(id=request.POST.get("edit-team"))
                if not acesso_team(request.user, team):
                    messages.error(request, "Você não tem permissão para editar este time.")
                    return redirect('team_manage')
                team.name = request.POST.get("edit-name")
                team.color = request.POST.get("edit-color")
                if request.FILES.get("edit-logo"):
                    team.photo = request.FILES.get("edit-logo")
                team.description = request.POST.get("edit-description")
                if request.POST.get('edit-status') == 'on':
                    team.status = True
                else:
                    team.status = False
                team.save()

            elif 'team-data' in request.POST:
                team_id = request.POST.get('team-data')
                team = Team.objects.get(id=team_id)
                if not acesso_team(request.user, team):
                    messages.error(request, "Você não tem permissão para acessar este time.")
                    return redirect('team_manage')

                cont = build_pdf_context(request, team.event)
                cont['team'] = team

                teams = Team_sport.objects.filter(team=team).prefetch_related(
                    Prefetch('players', queryset=Player_team_sport.objects.select_related('player'))
                ).order_by('sport__sport', '-sexo')

                cont['teams'] = teams
                name_html = 'data-base-teams'
                name_pdf = f'relatório do {team.name}'

                html_string = render_to_string(f'generator/{name_html}.html', cont)
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{name_pdf}.pdf"'
                HTML(string=html_string).write_pdf(response)
                return response

            elif 'team_sport_delete' in request.POST:
                team_sport_id = request.POST.get('team_sport_delete')
                team_sport_delete = Team_sport.objects.get(id=team_sport_id)
                if not acesso_team_sport(request.user, team_sport_delete):
                    messages.error(request, "Você não tem permissão para remover esta modalidade.")
                    return redirect('team_manage')
                players_team_sport = Player_team_sport.objects.filter(team_sport=team_sport_delete)
                if players_team_sport:
                    for i in players_team_sport:
                        i.delete()
                        if not Player_team_sport.objects.filter(player=i.player).exists():
                            status = verificar_foto(str(i.player.photo))
                            if status:
                                i.player.photo.delete()
                            i.player.bulletin.delete()
                            i.player.rg.delete()
                            i.player.delete()
                team_sport_delete.delete()
        except Exception as e:
            messages.error(request, f"Erro inesperado: {str(e)}")

        if current_get_params:
            return redirect(f"{reverse('team_manage')}?{current_get_params}")
        else:
            return redirect('team_manage')


@login_required(login_url="login")
@terms_accept_required
@permission_required('app.change_team_sport', raise_exception=True)
def team_edit(request, id):
    team_sport = get_object_or_404(Team_sport, id=id)

    if not request.user.is_superuser:
        if request.user.type == 2:
            if not request.user.team or team_sport.team != request.user.team:
                messages.error(request, "Você não tem permissão para acessar esse time.")
                return redirect('team_manage')
        elif request.user.type == 1:
            if not request.user.event_user or team_sport.event != request.user.event_user:
                messages.error(request, "Você não tem permissão para acessar esse time.")
                return redirect('team_manage')
        elif request.user.type != 0:
            messages.error(request, "Tipo de usuário inválido.")
            return redirect('team_manage')

    sport = Sport_types.choices
    campus = Campus_types.choices
    sexo = Sexo_types.choices
    users = User.objects.all()
    if request.method == 'GET':
        return render(request, 'team/team_edit.html', {
            'team_sport': team_sport, 'campus': campus,
            'sport': sport, 'sexo': sexo, 'users': users
        })
    else:
        try:
            team_sport.sport = request.POST.get('sport')
            team_sport.sexo = request.POST.get('sexo')
            team_sport.admin = User.objects.get(id=request.POST.get('user'))
            team_sport.team.campus = request.POST.get('campus')
            for i in campus:
                if i[0] == int(request.POST.get('campus')):
                    team_sport.team.name = i[1]
            team_sport.team.save()
            team_sport.save()
            messages.success(request, 'Alteração feita com sucesso!')
            return redirect('team_manage')
        except (TypeError, ValueError):
            messages.error(request, 'Um valor foi informado incorretamente!')
        except IntegrityError:
            messages.error(request, 'Algumas informações não foram preenchidas :(')
        except Exception as e:
            messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
    return redirect('team_manage')


@time_restriction()
@login_required(login_url="login")
@terms_accept_required
@permission_required('app.view_player_team_sport', raise_exception=True)
def team_players_manage(request, id):
    team_sport = get_object_or_404(Team_sport, id=id)

    if not acesso_team_sport(request.user, team_sport):
        messages.error(request, "Você não tem permissão para acessar esta modalidade.")
        return redirect('team_manage')

    # atualiza status de inscrição
    count_players = Player_team_sport.objects.filter(team_sport=team_sport).count()
    if count_players >= team_sport.sport.min_sport and not team_sport.status:
        team_sport.status = True
        team_sport.save()
    elif count_players < team_sport.sport.min_sport and team_sport.status:
        team_sport.status = False
        team_sport.save()

    user = User.objects.get(id=request.user.id)

    if request.method == "GET":
        player_team_sport = (
            Player_team_sport.objects
            .select_related('player', 'team_sport')
            .filter(team_sport=id)
        )
        context = {
            'player_team_sport': player_team_sport,
            'sexos': Sexo_types.choices,
            'team_sport': team_sport,
            'events': Event.objects.all(),
            'events_unit': Event_unit.objects.filter(event=team_sport.event),
        }
        return render(request, 'team/team_players_manage.html', context)

    # ── POST ──────────────────────────────────────────────────────────────────

    # ── remover jogador ───────────────────────────────────────────────────────
    if request.POST.get("player_delete"):
        player_id = request.POST.get('player_delete')
        Player_team_sport.objects.filter(team_sport=id, player=player_id).delete()
        if not Player_team_sport.objects.filter(player=player_id).exists():
            Player.objects.filter(id=player_id).delete()
        count_players = Player_team_sport.objects.filter(team_sport=team_sport).count()
        if count_players < team_sport.sport.min_sport and team_sport.status:
            team_sport.status = False
            team_sport.save()
        return redirect('team_players_manage', team_sport.id)

    # ── editar jogador existente ───────────────────────────────────────────────
    elif request.POST.get("edit-name"):
        player = Player.objects.get(id=request.POST.get("edit-player-id"))
        player.name = request.POST.get("edit-name")

        if team_sport.team.event.general_need_unit:
            player.unit = Event_unit.objects.get(id=int(request.POST.get('edit-unit')))

        if team_sport.team.event.player_need_address:
            player.address = request.POST.get('edit-address')

        if team_sport.team.event.player_need_registration:
            player.registration = request.POST.get("edit-registration")

        if team_sport.team.event.player_need_date_nasc:
            date_nasc = dt_module.strptime(request.POST.get("edit-date"), "%Y-%m-%d").date()
            idade = calcular_idade(date_nasc)

            if idade < team_sport.team.event.age:
                messages.error(request, "Não foi possível atualizar: idade abaixo do mínimo.")
                return redirect('team_players_manage', team_sport.id)

            if idade > team_sport.team.event.age_max:
                messages.error(request, "Não foi possível atualizar: idade acima do máximo permitido.")
                return redirect('team_players_manage', team_sport.id)

            player.date_nasc = date_nasc

        if team_sport.team.event.player_need_photo and request.FILES.get("edit-photo"):
            player.photo = request.FILES.get("edit-photo")

        if team_sport.team.event.player_need_course and request.POST.get("edit-course"):
            player.course = request.POST.get('edit-course')

        if team_sport.team.event.player_need_cpf:
            cpf = (request.POST.get('edit-cpf') or '').replace("-", "").replace(".", "").strip()
            if len(cpf) != 11:
                messages.error(request, "CPF inválido! Deve conter 11 números.")
                return redirect('team_players_manage', team_sport.id)
            player.cpf = cpf

        if team_sport.team.event.player_need_cep:
            player.cep = (request.POST.get('edit-cep') or '').replace("-", "").replace(".", "").replace(" ", "")

        if team_sport.team.event.player_need_municipality:
            player.municipality = request.POST.get('edit-municipality')

        if team_sport.team.event.player_need_photo_goal and request.FILES.get("edit-photo-goal"):
            player.photo_goal = request.FILES.get("edit-photo-goal")

        if team_sport.team.event.player_need_bulletin and request.FILES.get("edit-bulletin"):
            player.bulletin = request.FILES.get("edit-bulletin")

        if team_sport.team.event.player_need_rg and request.FILES.get("edit-rg"):
            player.rg = request.FILES.get("edit-rg")

        player.save()
        messages.success(request, "Atleta atualizado com sucesso!")
        return redirect('team_players_manage', team_sport.id)

    # ── buscar jogador existente no sistema ────────────────────────────────────
    elif 'search' in request.POST:
        count_players = Player_team_sport.objects.filter(team_sport=team_sport).count()
        if count_players >= team_sport.sport.max_sport:
            messages.error(request, "O time atingiu o limite de atletas nessa modalidade!")
            return redirect('team_players_manage', team_sport.id)

        qe = request.POST.get('search')
        admin_filter = None if user.type in (0, 1) else user

        base_qs = player_queryset_for_team(
            team_sport, user, team_sport.team.event, admin_user=admin_filter
        )

        if qe.isdigit():
            player_filter = base_qs.filter(registration=int(qe))
        else:
            player_filter = base_qs.filter(name__icontains=qe)

        if player_filter.count() > 1:
            messages.error(
                request,
                f"{player_filter.count()} atletas encontrados — seja mais preciso "
                f"(use nome completo ou matrícula)."
            )
        elif not player_filter.exists():
            messages.error(request, "Atleta não encontrado ou incompatível com o sexo do time.")
        else:
            player = player_filter.first()
            ok, err = check_gender_compatibility(player, team_sport, user)
            if not ok:
                messages.error(request, err)
            elif Player_team_sport.objects.filter(player=player, team_sport=team_sport).exists():
                messages.info(request, f"O atleta '{player.name}' já está nessa modalidade.")
            else:
                Player_team_sport.objects.create(player=player, team_sport=team_sport)
                messages.success(request, f"Atleta '{player.name}' adicionado com sucesso!")

        return redirect('team_players_manage', team_sport.id)

    # ── criar novo jogador ─────────────────────────────────────────────────────
    elif 'name' in request.POST:
        count_players = Player_team_sport.objects.filter(team_sport=team_sport).count()
        if count_players >= team_sport.sport.max_sport:
            messages.error(request, "O time atingiu o limite de atletas nessa modalidade!")
            return redirect('team_players_manage', team_sport.id)

        # validações de arquivo
        if team_sport.team.event.player_need_date_nasc:
            date_nasc = dt_module.strptime(request.POST.get('date'), "%Y-%m-%d").date()
            idade = calcular_idade(date_nasc)

            if idade < team_sport.team.event.age:
                messages.error(request, "O atleta não pode ser cadastrado: idade abaixo do mínimo.")
                return redirect('team_players_manage', team_sport.id)

            if idade > team_sport.team.event.age_max:
                messages.error(request, "O atleta não pode ser cadastrado: idade acima do máximo permitido.")
                return redirect('team_players_manage', team_sport.id)

        for field, exts, label in [
            ('photo',      ['.png', '.jpg', '.jpeg'], 'A foto deve ser PNG, JPG ou JPEG.'),
            ('photo_goal', ['.png', '.jpg', '.jpeg'], 'A foto gol deve ser PNG, JPG ou JPEG.'),
            ('bulletin',   ['.pdf'],                  'O boletim deve ser PDF.'),
            ('rg',         ['.png', '.jpg', '.jpeg', '.pdf', '.docx'], 'Formato de RG inválido.'),
        ]:
            if team_sport.team.event.__dict__.get(f'player_need_{field}', False):
                f = request.FILES.get(field)
                if f and type_file(request, exts, f, label):
                    return redirect('team_players_manage', team_sport.id)

        # sexo do jogador
        sexo_jogador = None

        if team_sport.sexo in (0, 1):
            sexo_jogador = team_sport.sexo
        else:
            raw = request.POST.get('sexo')
            if raw in (None, '', 'None'):
                messages.error(request, "Em times mistos, selecione o sexo do atleta.")
                return redirect('team_players_manage', team_sport.id)
            try:
                sexo_jogador = int(raw)
            except (TypeError, ValueError):
                messages.error(request, "Selecione um sexo válido para o atleta.")
                return redirect('team_players_manage', team_sport.id)
            if sexo_jogador not in (0, 1):
                messages.error(request, "Selecione um sexo válido para o atleta.")
                return redirect('team_players_manage', team_sport.id)

        # validação de gênero antes de criar
        if not user.is_superuser:
            if team_sport.sexo in (0, 1) and sexo_jogador != team_sport.sexo:
                messages.error(
                    request,
                    f"O sexo do atleta é incompatível com o time "
                    f"({SEXO_NAMES[team_sport.sexo]})."
                )
                return redirect('team_players_manage', team_sport.id)

        name = request.POST.get('name')
        photo = request.FILES.get('photo')
        photo_goal = request.FILES.get('photo_goal')
        bulletin = request.FILES.get('bulletin')
        rg = request.FILES.get('rg')

        player, created = Player.objects.get_or_create(
            name=name, admin=user, event=team_sport.event,
        )

        if team_sport.team.event.general_need_unit:
            if user.type == 2:
                player.unit = Event_unit.objects.get(id=user.unit.id)
            else:
                player.unit = Event_unit.objects.get(id=int(request.POST.get('unit')))

        if team_sport.team.event.player_need_date_nasc:
            player.date_nasc = date_nasc
        if team_sport.team.event.player_need_address:
            player.address = request.POST.get('address')
        if team_sport.team.event.player_need_registration:
            player.registration = request.POST.get('registration')
        if team_sport.team.event.player_need_cpf:
            cpf = (request.POST.get('cpf') or '').replace("-", "").replace(".", "").strip()
            if len(cpf) != 11:
                messages.error(request, "CPF inválido! Deve conter 11 números.")
                return redirect('team_players_manage', team_sport.id)
            player.cpf = cpf

        if team_sport.team.event.player_need_photo and photo:
            player.photo = photo
        if team_sport.team.event.player_need_course:
            player.course = request.POST.get('course')
        if team_sport.team.event.player_need_cep:
            player.cep = (request.POST.get('cep') or '').replace("-", "").replace(".", "").replace(" ", "")
        if team_sport.team.event.player_need_municipality:
            player.municipality = request.POST.get('municipality')
        if team_sport.team.event.player_need_photo_goal and photo_goal:
            player.photo_goal = photo_goal
        if team_sport.team.event.player_need_bulletin and bulletin:
            player.bulletin = bulletin
        if team_sport.team.event.player_need_rg and rg:
            player.rg = rg

        player.sexo = sexo_jogador

        if player.sexo is None:
            messages.error(request, "Não foi possível cadastrar o atleta sem sexo definido.")
            return redirect('team_players_manage', team_sport.id)

        player.save()

        _, vinculo_criado = Player_team_sport.objects.get_or_create(
            player=player, team_sport=team_sport
        )
        if vinculo_criado:
            messages.success(request, "Atleta cadastrado com sucesso!")
        else:
            messages.info(request, "O atleta já estava nessa modalidade.")

        # reavalia status
        count_players = Player_team_sport.objects.filter(team_sport=team_sport).count()
        if count_players >= team_sport.sport.min_sport and not team_sport.status:
            team_sport.status = True
            team_sport.save()

        return redirect('team_players_manage', team_sport.id)

    return redirect('team_players_manage', team_sport.id)


@login_required(login_url="login")
@terms_accept_required
@permission_required('app.add_player_team_sport', raise_exception=True)
def add_player_team(request, id):
    team = get_object_or_404(Team_sport, id=id)
    players = Player.objects.all()
    if request.method == 'GET':
        if not players:
            messages.info(request, "Não tem nenhum atleta cadastrado no sistema!")
        return render(request, 'add_players_team.html', {'players': players, 'team': team})
    else:
        try:
            player_ids = request.POST.getlist('input-checkbox')
            for pid in player_ids:
                player = Player.objects.get(id=pid)
                Player_team_sport.objects.create(player=player, team_sport=team)
        except (TypeError, ValueError):
            messages.error(request, 'Um valor foi informado incorretamente!')
        except IntegrityError:
            messages.error(request, 'Algumas informações não foram preenchidas :(')
        except Exception as e:
            messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return redirect('team_players_manage', team.id)
