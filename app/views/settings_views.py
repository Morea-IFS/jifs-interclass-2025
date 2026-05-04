"""
Views extraídas automaticamente do views.py monolítico.
Módulo: settings_views.py
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
def theme_manage(request):
    return render(request, 'settings/theme.html')

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
@permission_required('app.add_attachments', raise_exception=True)
def anexo_register(request):
    if request.method == "GET":
        return render(request, 'settings/anexo_register.html')
    else:
        try:
            title_atack = request.POST.get('title_atack')
            file_atack = request.FILES.get('file_atack')
            Attachments.objects.create(name=title_atack, user=request.user, file=file_atack)
            messages.success(request, "Parabéns, foi cadastrado com sucesso!")
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
@permission_required('app.add_settings_access', raise_exception=True)
def enrollment_register(request):
    if request.method == "GET":
        return render(request, 'settings/enrollment_register.html')
    else:
        try:
            start = request.POST.get('date_start')
            end = request.POST.get('date_end')
            Settings_access.objects.create(start=start, end=end)
            messages.success(request, "Parabéns, foi cadastrado com sucesso!")
            return redirect('enrollment_manage')
        except Exception as e: messages.error(request, f'Um erro inesperado aconteceu: {str(e)}')
        return redirect('enrollment_manage')

@login_required(login_url="login")
@terms_accept_required
def attachments(request):
    if request.method == "GET":
        context = {}
        if request.user.type == 0 or request.user.is_staff:  
            context['events'] = Event.objects.all()
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
