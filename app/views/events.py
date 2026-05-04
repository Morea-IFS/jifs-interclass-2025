"""Views de gerenciamento de eventos."""

import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from app.decorators import terms_accept_required
from app.models import (
    Event,
    Event_badge,
    Event_sport,
    Event_unit,
    Sport_types,
    Team,
)
from app.services.password import generate_random_password
from app.services.pdf import build_pdf_context, generate_pdf_response, generate_qr_base64

logger = logging.getLogger(__name__)
User = get_user_model()


@login_required(login_url="login")
@permission_required('app.view_event', raise_exception=True)
def event_manage(request):
    if request.method == "GET":
        events = Event.objects.all()
        events_unit = Event.objects.filter(general_need_unit=True)
        return render(request, 'events/event_manage.html', {
            'events': events,
            'events_unit': events_unit,
            'sports': Sport_types.choices,
            'event_badges': Event_badge.objects.all(),
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
        if 'reset_badge' in request.POST:
            badge = get_object_or_404(Event_badge, id=request.POST.get('reset_badge'))

            if badge.file:
                badge.file.delete(save=False)

            badge.delete()
            messages.success(request, "Crachá resetado para o padrão com sucesso.")
        elif 'event_badge' in request.POST:
            event_badge = request.POST.get("event_badge")
            type_badge = request.POST.get("type_badge")
            image_badge = request.FILES.get("image_badge")
            if image_badge and type_badge and image_badge:
                if Event_badge.objects.filter(event=Event.objects.get(id=event_badge), number=type_badge):
                    event_badge_obj = Event_badge.objects.filter(event=Event.objects.get(id=event_badge), number=type_badge)[0]
                    event_badge_obj.file = image_badge
                    event_badge_obj.save()
                    messages.success(request, f"Sucesso! o crachá já existe. sendo assim, apenas a imagem foi trocada.")
                else:
                    Event_badge.objects.create(event=Event.objects.get(id=event_badge), number=type_badge, file=image_badge)
                    messages.success(request, f"Sucesso! o crachá foi cadastrado!.")
            else:
                messages.error(request, f"Erro! algumas informações não foram enviadas. :(")

        elif 'event_unit' in request.POST:
            try:
                event_unit_id = int(request.POST.get('event_unit'))
            except (ValueError, TypeError):
                messages.error(request, "ID de evento inválido.")
                return redirect('event_manage')
            event = Event.objects.get(id=event_unit_id)
            name_unit = request.POST.get('name_unit').replace(" ", "").replace(".", "").replace("-", "")
            create_team_user = 'create-team-user' in request.POST
            if Event_unit.objects.filter(event=event, name=name_unit):
                event_unit = Event_unit.objects.get(event=event, name=name_unit)
            else:
                event_unit = Event_unit.objects.create(
                    event=event,
                    name=name_unit,
                )
            event_unit.save()
            if create_team_user:
                if Team.objects.filter(name=name_unit, unit=event_unit, event=event):
                    if User.objects.filter(username=f"admin.{name_unit.lower()}{event.id}", type=2, team=Team.objects.get(name=name_unit, unit=event_unit, event=event), event_user=event, unit=event_unit):
                        messages.info(request, f"Erro! Já existe um time e um usuário que está associada a unidade.")
                        return redirect('event_manage')
                team = Team.objects.create(name=name_unit, unit=event_unit, event=event, status=False)
                team.save()
                result = generate_random_password(8)
                user = User.objects.create_user(
                    username=f"admin.{name_unit.lower()}{event.id}",
                    password=result, type=2, team=team,
                    event_user=event, unit=event_unit
                )
                messages.success(request, f"Sucesso! Unidade cadastrada com exito.")

                cont = build_pdf_context(request, event)

                link = f"https://{request.get_host()}"
                cont['site'] = link
                cont['qrcode'] = generate_qr_base64(link)
                cont['name'] = user.username
                cont['password'] = result

                return generate_pdf_response(
                    'data-welcome', cont,
                    f'boas vindas, {name_unit.lower()}',
                    attachment=True
                )

        elif 'name' in request.POST:
            name = request.POST.get('name')
            logo = request.FILES.get('logo')
            logo_badge = request.FILES.get('logo_badge')
            description = request.POST.get('description')
            date_init = request.POST.get('date_init')
            date_end = request.POST.get('date_end')
            enrollment_init = request.POST.get('enrollment_init')
            enrollment_end = request.POST.get('enrollment_end')
            local = request.POST.get('local')
            age = request.POST.get('age')
            age_max = request.POST.get('age_max')
            regulation = request.FILES.get('regulation')

            player_need_instagram = 'player_need_instagram' in request.POST
            player_need_photo = 'player_need_photo' in request.POST
            player_need_bulletin = 'player_need_bulletin' in request.POST
            player_need_rg = 'player_need_rg' in request.POST
            player_need_sexo = 'player_need_sexo' in request.POST
            player_need_registration = 'player_need_registration' in request.POST
            player_need_cpf = 'player_need_cpf' in request.POST
            player_need_date_nasc = 'player_need_date_nasc' in request.POST
            player_need_address = 'player_need_address' in request.POST
            player_need_photo_goal = 'player_need_photo_goal' in request.POST
            player_need_course = 'player_need_course' in request.POST
            player_need_cep = 'player_need_cep' in request.POST
            player_need_municipality = 'player_need_municipality' in request.POST

            general_need_authorization = 'general_need_authorization' in request.POST
            general_need_terms = 'general_need_terms' in request.POST
            general_need_unit = 'general_need_unit' in request.POST

            team_need_description = 'team_need_description' in request.POST
            team_need_color = 'team_need_color' in request.POST
            team_need_technician = 'team_need_technician' in request.POST

            terms_intro_text = request.POST.get('terms_intro_text', '').strip() or None
            terms_declaration_text = request.POST.get('terms_declaration_text', '').strip() or None
            upload_intro_text = request.POST.get('upload_intro_text', '').strip() or None

            tutorial = request.POST.get('tutorial', '').strip() or None

            Event.objects.create(
                name=name, logo=logo, logo_badge=logo_badge,
                description=description, date_init=date_init,
                date_end=date_end, enrollment_init=enrollment_init,
                enrollment_end=enrollment_end, local=local,
                age=age, age_max=age_max, regulation=regulation,
                user=request.user,
                player_need_instagram=player_need_instagram,
                player_need_photo=player_need_photo,
                player_need_bulletin=player_need_bulletin,
                player_need_rg=player_need_rg,
                player_need_sexo=player_need_sexo,
                player_need_registration=player_need_registration,
                player_need_cpf=player_need_cpf,
                player_need_date_nasc=player_need_date_nasc,
                player_need_address=player_need_address,
                player_need_photo_goal=player_need_photo_goal,
                player_need_course=player_need_course,
                player_need_cep=player_need_cep,
                player_need_municipality=player_need_municipality,
                general_need_authorization=general_need_authorization,
                general_need_terms=general_need_terms,
                general_need_unit=general_need_unit,
                team_need_description=team_need_description,
                team_need_color=team_need_color,
                team_need_technician=team_need_technician,
                terms_intro_text=terms_intro_text,
                terms_declaration_text=terms_declaration_text,
                upload_intro_text=upload_intro_text,
                tutorial=tutorial,
            )

        return redirect('event_manage')


@login_required(login_url="login")
def event_sport_manage(request):
    return render(request, 'events/event_manage.html')


@login_required(login_url="login")
def event_sport_edit(request):
    return render(request, 'events/event_manage.html')
