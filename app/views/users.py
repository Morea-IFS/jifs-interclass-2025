"""Views de gerenciamento de usuários e sessões."""

import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.sessions.models import Session
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from app.decorators import time_restriction, terms_accept_required
from app.helpers import verificar_foto
from app.models import (
    Event,
    Event_unit,
    Team,
    Users_types,
    UserSession,
    Voluntary,
)
from app.services.password import generate_random_password
from app.services.pdf import build_pdf_context, generate_pdf_response, generate_qr_base64

logger = logging.getLogger(__name__)
User = get_user_model()


@login_required(login_url="login")
def manage_session(request):
    current_get_params = request.GET.urlencode()
    if request.method == "GET":
        context = {'users': User.objects.all()}
        if 'e' in request.GET and request.GET.get('e') != '':
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
    context = {
        'events': Event.objects.all(),
    }
    if request.user.type not in [0]:
        context['type_user'] = Users_types.choices[2:]
        context['team'] = Team.objects.filter(event__id=request.user.event_user.id)
        context['event_unit'] = Event_unit.objects.filter(event__id=request.user.event_user.id)
        context['users_all'] = User.objects.filter(event_user=request.user.event_user)
        context['terms'] = Voluntary.objects.filter(event=request.user.event_user, type_voluntary=4)
    elif 'e' in request.GET and request.GET['e'] != '':
        context['type_user'] = Users_types.choices
        context['users_all'] = User.objects.filter(event_user=Event.objects.get(id=request.GET['e']))
        context['select_event'] = request.GET['e']
        context['event_unit'] = Event_unit.objects.filter(event__id=request.GET['e'])
        context['team'] = Team.objects.filter(event__id=request.GET['e'])
        context['terms'] = Voluntary.objects.filter(event__id=request.GET['e'], type_voluntary=4)
    else:
        context['type_user'] = Users_types.choices
        context['users_all'] = User.objects.filter(event_user=None)
        context['terms'] = Voluntary.objects.none()

    if request.method == "GET":
        return render(request, 'settings/user_manage.html', context)
    else:
        if 'user_id' in request.POST:
            user = get_object_or_404(User, id=request.POST.get('user_id'))
            # type 1 só pode editar usuários do próprio evento
            if request.user.type == 1:
                if user.event_user != request.user.event_user:
                    messages.error(request, "Você não tem permissão para editar este usuário.")
                    return redirect('user_manage')
            if request.POST.get('name'):
                user.username = str(request.POST.get('name'))
            if request.POST.get('password'):
                senha = request.POST.get('password')
                user.set_password(senha)
            event_val = request.POST.get('event')
            try:
                if event_val and int(event_val) != 0:
                    user.event_user = Event.objects.get(id=int(event_val))
                else:
                    user.event_user = None
            except (ValueError, TypeError, Event.DoesNotExist):
                messages.error(request, "Evento inválido.")
                return redirect('user_manage')
            if request.POST.get('telephone'):
                user.telefone = request.POST.get('telephone')
            if request.POST.get('registration'):
                Voluntary.objects.filter(
                    admin=user,
                    event=user.event_user,
                    type_voluntary=4
                ).update(registration=request.POST.get('registration'))
            if request.POST.get('email'):
                user.email = str(request.POST.get('email'))
            if request.POST.get('active') == 'on':
                user.is_active = True
            else:
                user.is_active = False
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
            messages.success(request, f"{user.username} do sistema atualizado com sucesso!")
        elif 'name' in request.POST:
            try:
                name = request.POST.get('name')
                event_val = request.POST.get('event')
                if event_val and int(event_val) != 0:
                    event = Event.objects.get(id=int(event_val))
                elif request.user.type == 1:
                    event = request.user.event_user
                else:
                    event = None
                type_val = request.POST.get('type')
                if not type_val:
                    messages.error(request, "Tipo de usuário não informado.")
                    return redirect('user_manage')
                team = request.POST.get('team')
                email = request.POST.get('email')
                telephone = request.POST.get('telephone')
                password = request.POST.get('password')
                photo = request.FILES.get('photo')
                if int(type_val) == 2:
                    if team:
                        User.objects.create_user(username=name, password=password, photo=photo, type=type_val, team=Team.objects.get(id=team), email=email, telefone=telephone, event_user=event)
                    elif request.user.team:
                        User.objects.create_user(username=name, password=password, photo=photo, type=type_val, team=request.user.team, email=email, telefone=telephone, event_user=event)
                    else:
                        messages.error(request, "Você não informou o time associado ao usuário.")
                else:
                    User.objects.create_user(username=name, password=password, photo=photo, type=type_val, email=email, telefone=telephone, event_user=event)
                    messages.success(request, f"{name} cadastrado do sistema com sucesso!")
            except (ValueError, TypeError) as e:
                messages.error(request, f"Dado inválido: {str(e)}")
            except Event.DoesNotExist:
                messages.error(request, "Evento não encontrado.")
            except Exception as e:
                messages.error(request, f"Erro inesperado: {str(e)}")
        elif 'new_password' in request.POST:
            user = User.objects.get(id=request.POST.get('new_password'))
            result = generate_random_password(8)

            user.set_password(result)
            user.save()
            messages.success(request, f"Sucesso! Senha gerada com exito.")

            cont = build_pdf_context(request, user.event_user)

            link = f"https://{request.get_host()}"
            cont['site'] = link
            cont['qrcode'] = generate_qr_base64(link)
            cont['name'] = user.username
            cont['password'] = result

            return generate_pdf_response(
                'data-welcome', cont,
                f'boas vindas, {user.username.lower()}',
                attachment=True
            )

        elif 'user_delete' in request.POST:
            user_id = request.POST.get('user_delete')
            user_delete = User.objects.get(id=user_id)
            user_delete.delete()
            messages.info(request, f"{user_delete.username} removido do sistema com sucesso!")
        return redirect('user_manage')
