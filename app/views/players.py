"""Views de gerenciamento de jogadores."""

import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404

from app.decorators import terms_accept_required
from app.helpers import acesso_player, verificar_foto, type_file
from app.models import Campus_types, Event, Player

logger = logging.getLogger(__name__)
User = get_user_model()


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
                player_delete = get_object_or_404(Player, id=player_id)
                if not acesso_player(request.user, player_delete):
                    messages.error(request, "Você não tem permissão para remover este atleta.")
                    return redirect('player_manage')
                status = verificar_foto(str(player_delete.photo))
                if status:
                    player_delete.photo.delete()
                player_delete.delete()
                messages.success(request, "Atleta removido com sucesso!")
            return redirect('player_manage')
        except Exception as e:
            messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return redirect('player_manage')


@login_required(login_url="login")
@terms_accept_required
@permission_required('app.change_player', raise_exception=True)
def player_edit(request, id):
    try:
        campus = Campus_types.choices
        player = get_object_or_404(Player, id=id)
        if not acesso_player(request.user, player):
            messages.error(request, "Você não tem permissão para editar este atleta.")
            return redirect('player_manage')
        if request.method == 'GET':
            return render(request, 'players/player_edit.html', {'player': player, 'campus': campus})
        else:
            player.name = request.POST.get('name')
            player.sexo = request.POST.get('sexo')
            player.registration = request.POST.get('registration')
            player.cpf = request.POST.get('cpf')
            photo = request.FILES.get('photo')
            if photo:
                status = type_file(request, ['.png', '.jpg', '.jpeg'], photo,
                                   'A photo anexada não é do tipo png, jpg ou jpeg, considere converte-la em um desses tipos.')
                if not status:
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
    except Exception as e:
        messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
    return redirect('Home')
