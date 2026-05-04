"""Views de API (JSON endpoints)."""

import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from app.helpers import player_queryset_for_team
from app.models import (
    Event_sport,
    Group_phase,
    Player_team_sport,
    Team_sport,
)

logger = logging.getLogger(__name__)


@login_required(login_url="login")
def get_teams(request):
    sport_id = request.GET.get('sport')
    sexo = request.GET.get('sexo')
    teams = Team_sport.objects.filter(sport__id=sport_id, sexo=sexo)
    data = {"teams": [{"id": t.team.id, "name": t.team.name} for t in teams]}
    return JsonResponse(data)


@login_required(login_url="login")
def get_groups(request):
    sport_id = request.GET.get('sport')
    groups = Group_phase.objects.filter(
        phase__event__id=sport_id
    ).order_by('phase__name', 'phase__event', 'phase__sexo')
    data = [
        {
            "id": g.id,
            "name": g.name,
            "phase_name": g.phase.get_name_display(),
            "sexo": g.phase.get_sexo_display(),
        }
        for g in groups
    ]
    return JsonResponse({"groups": data})


@login_required(login_url="login")
def get_sexos(request):
    sport_id = request.GET.get('sport')
    esport = Event_sport.objects.get(id=sport_id)

    sexos = []
    if esport.masc:
        sexos.append({"value": 0, "label": "Masculino"})
    if esport.fem:
        sexos.append({"value": 1, "label": "Feminino"})
    if esport.mist:
        sexos.append({"value": 2, "label": "Misto"})

    return JsonResponse({"sexos": sexos})


@login_required(login_url="login")
def search_player_preview(request, team_sport_id):
    team_sport = get_object_or_404(Team_sport, id=team_sport_id)
    q = request.GET.get('q', '').strip()

    if not q:
        return JsonResponse({'found': False, 'message': 'Digite o nome ou matrícula.'})

    user = request.user
    admin_filter = None if user.type in (0, 1) else user

    base_qs = player_queryset_for_team(
        team_sport, user, team_sport.team.event, admin_user=admin_filter
    )

    if q.isdigit():
        player_filter = base_qs.filter(registration=int(q))
    else:
        player_filter = base_qs.filter(name__icontains=q)

    if player_filter.count() > 1:
        return JsonResponse({
            'found': False,
            'message': f'{player_filter.count()} atletas encontrados — seja mais preciso (use nome completo ou matrícula).'
        })
    elif not player_filter.exists():
        return JsonResponse({
            'found': False,
            'message': 'Atleta não encontrado ou incompatível com o sexo do time.'
        })
    else:
        player = player_filter.first()
        if Player_team_sport.objects.filter(player=player, team_sport=team_sport).exists():
            return JsonResponse({
                'found': False,
                'message': f"O atleta '{player.name}' já está nessa modalidade."
            })
        return JsonResponse({
            'found': True,
            'name': player.name,
            'registration': player.registration or ''
        })
