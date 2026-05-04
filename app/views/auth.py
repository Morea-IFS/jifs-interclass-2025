"""Views de autenticação, login, logout, termos de uso."""

import logging

from django.contrib import messages
from django.contrib.auth import (
    login as auth_login,
    authenticate,
    logout,
    get_user_model,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from app.decorators import terms_accept_required
from app.helpers import type_file, verificar_foto
from app.models import Event, Voluntary

logger = logging.getLogger(__name__)
User = get_user_model()


def login(request):
    if not request.user.is_authenticated:
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
                next_url = request.GET.get('next') or '/morea-admin'
                return redirect(next_url)
            else:
                messages.error(request, "Poxa! algo está errado, pode ser o usuário ou a senha.")
                return redirect('login')
    else:
        next_url = request.GET.get('next') or '/morea-admin'
        return redirect(next_url)


@login_required(login_url="login")
@terms_accept_required
def sair(request):
    logout(request)
    return redirect('events')


def has_accepted_terms(user, request):
    try:
        user_accepted = User.objects.get(id=request.user.id)
        return bool(user_accepted.document and user_accepted.photo and user_accepted.accepted)
    except Exception:
        return False


@login_required(login_url="login")
def upload_document(request):
    termo = User.objects.get(id=request.user.id)
    if not request.user.event_user.general_need_authorization:
        return redirect('boss_data')
    if termo.document:
        return redirect('boss_data')

    if request.method == 'POST':
        document = request.FILES.get('document')
        if document:
            termo.document = document
            if document:
                status = type_file(request, ['.pdf', '.png', '.jpg', '.jpeg'], document,
                                   'O documento anexado precisa ser do tipo pdf, png, jpg ou jpeg.')
                if status:
                    return redirect('upload_document')
            termo.save()
            return redirect('boss_data')

    return render(request, 'terms/terms_use_upload.html')


@login_required(login_url="login")
def boss_data(request):
    termo = User.objects.get(id=request.user.id)
    if request.user.event_user.general_need_authorization:
        if not termo.document:
            return redirect('upload_document')
    if termo.email and termo.photo and termo.telefone:
        return redirect('terms_use')

    if request.method == 'POST':
        password = request.POST.get('password')
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        photo = request.FILES.get('photo')

        if password and photo and email and phone and name:
            termo.first_name = name
            termo.email = email
            termo.telefone = phone
            request.session['registration'] = request.POST.get('registration') or ''
            if photo:
                status = type_file(request, ['.png', '.jpg', '.jpeg'], photo,
                                   'A photo anexada não é do tipo png, jpg ou jpeg, considere converte-la em um desses tipos.')
                if status:
                    return redirect('boss_data')
            termo.photo = photo
            termo.set_password(password)
            termo.save()
            update_session_auth_hash(request, termo)
            return redirect('terms_use')
        else:
            messages.error(request, 'Você precisa preencher todas as informações!')
            return redirect('boss_data')

    return render(request, 'terms/terms_use_data.html')


@login_required(login_url="login")
def terms_use(request):
    user = User.objects.get(id=request.user.id)
    if request.user.event_user.general_need_authorization:
        if not user.document:
            return redirect('upload_document')
    if not (user.email and user.photo and user.telefone and user.first_name):
        return redirect('boss_data')
    if user.accepted:
        return redirect('Home')

    if request.method == 'POST':
        if request.POST.get('accept') == 'on':
            user.accepted = True
            user.accepted_at = timezone.now()
            user.save()

            Voluntary.objects.create(
                name=user.first_name,
                photo=user.photo,
                unit=user.unit,
                admin=request.user,
                event=user.event_user,
                type_voluntary=4,
                registration=request.session.pop('registration', ''),
            )

            return redirect('Home')

    return render(request, 'terms/terms_use.html', {'termo': user})
