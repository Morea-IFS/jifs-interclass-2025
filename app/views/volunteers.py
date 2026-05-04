"""Views de gerenciamento de voluntários / comissão técnica."""

import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from app.decorators import time_restriction, terms_accept_required
from app.helpers import verificar_foto, type_file
from app.models import (
    Event,
    Event_unit,
    Type_service,
    Voluntary,
)

logger = logging.getLogger(__name__)
User = get_user_model()


@time_restriction()
@login_required(login_url="login")
@terms_accept_required
@permission_required('app.view_voluntary', raise_exception=True)
def voluntary_manage(request):
    user = User.objects.get(id=request.user.id)

    # tipos disponíveis para cadastro (chefe de delegação só para staff)
    if user.is_staff:
        types = Type_service.choices
    else:
        types = [choice for choice in Type_service.choices if choice[0] != 4]

    # ── GET ───────────────────────────────────────────────────────────────────
    if request.method == "GET":
        context = {
            'types': types,
            'users': User.objects.all(),
        }

        # ── type=0 (admin): escolhe evento via ?e= ────────────────────────────
        if user.type == 0:
            context['events'] = Event.objects.all()

            e = request.GET.get('e', '').strip()
            q = request.GET.get('q', '').strip()

            if e:
                context['select_event'] = e
                context['events_unit'] = Event_unit.objects.filter(event__id=e)

                qs = Voluntary.objects.filter(event__id=e)
                if q:
                    qs = qs.filter(name__icontains=q)

                # filtra por unidade específica se ?u= for passado
                u_param = request.GET.get('u', '').strip()
                if u_param:
                    qs = qs.filter(unit__id=u_param)
                    context['select_unit'] = u_param

                context['voluntarys'] = qs.order_by('unit__name', 'type_voluntary', 'name')

        # ── type=1 (coordenador): vê todas as unidades do próprio evento ──────
        elif user.type == 1:
            event = user.event_user
            if event:
                context['event'] = event
                context['events_unit'] = Event_unit.objects.filter(event=event)

                q = request.GET.get('q', '').strip()
                qs = Voluntary.objects.filter(event=event)

                if q:
                    qs = qs.filter(name__icontains=q)

                # filtro opcional por unidade
                u_param = request.GET.get('u', '').strip()
                if u_param:
                    qs = qs.filter(unit__id=u_param)
                    context['select_unit'] = u_param

                context['voluntarys'] = qs.order_by('unit__name', 'type_voluntary', 'name')

        # ── type=2 (usuário comum): vê apenas a própria unidade ───────────────
        else:
            event = user.event_user
            if event and user.unit:
                context['event'] = event

                q = request.GET.get('q', '').strip()
                qs = Voluntary.objects.filter(event=event, unit=user.unit)

                if q:
                    qs = qs.filter(name__icontains=q)

                context['voluntarys'] = qs.order_by('type_voluntary', 'name')

        return render(request, 'voluntary/voluntary_manage.html', context)

    # ── POST ──────────────────────────────────────────────────────────────────
    # monta URL de redirect preservando filtros
    e_param = request.GET.get('e') or request.POST.get('event') or ''
    u_param = request.GET.get('u', '')
    redirect_url = f"{reverse('voluntary_manage')}?e={e_param}"
    if u_param:
        redirect_url += f"&u={u_param}"

    # ── deletar ───────────────────────────────────────────────────────────────
    if 'voluntary_delete' in request.POST:
        if not request.user.has_perm('app.delete_voluntary'):
            messages.error(request, "Você não tem permissão para remover.")
            return redirect(redirect_url)

        voluntary_id = request.POST.get('voluntary_delete')
        voluntary_delete = get_object_or_404(Voluntary, id=voluntary_id)

        # type=2 só pode deletar da sua unidade
        if user.type == 2 and voluntary_delete.unit != user.unit:
            messages.error(request, "Você não tem permissão para remover membros de outra unidade.")
            return redirect(redirect_url)

        # type=1 só pode deletar do seu evento
        if user.type == 1 and voluntary_delete.event != user.event_user:
            messages.error(request, "Você não tem permissão para remover membros de outro evento.")
            return redirect(redirect_url)

        status = verificar_foto(str(voluntary_delete.photo))
        if status:
            voluntary_delete.photo.delete()
        voluntary_delete.delete()
        messages.success(request, f"{voluntary_delete.get_type_voluntary_display()} removido com sucesso!")

    # ── editar ────────────────────────────────────────────────────────────────
    elif 'voluntary_id' in request.POST:
        try:
            v_id = int(request.POST.get("voluntary_id"))
        except (ValueError, TypeError):
            messages.error(request, "ID inválido.")
            return redirect(redirect_url)
        voluntary = get_object_or_404(Voluntary, id=v_id)

        # validação de escopo
        if user.type == 2 and voluntary.unit != user.unit:
            messages.error(request, "Você não pode editar membros de outra unidade.")
            return redirect(redirect_url)
        if user.type == 1 and voluntary.event != user.event_user:
            messages.error(request, "Você não pode editar membros de outro evento.")
            return redirect(redirect_url)

        voluntary.name = request.POST.get('name')
        voluntary.registration = request.POST.get('registration')
        voluntary.type_voluntary = request.POST.get('type_voluntary')

        # admin pode trocar usuário responsável e evento
        if user.is_staff:
            voluntary.admin = User.objects.get(id=request.POST.get('user'))
            voluntary.event = Event.objects.get(id=request.POST.get('event'))

        # atualiza unidade se enviada
        unit_id = request.POST.get('unit')
        if unit_id:
            voluntary.unit = get_object_or_404(Event_unit, id=unit_id)

        photo = request.FILES.get('photo')
        if photo:
            err = type_file(request, ['.png', '.jpg', '.jpeg'], photo,
                            'A foto deve ser PNG, JPG ou JPEG.')
            if err:
                return redirect(redirect_url)
            if voluntary.photo:
                if verificar_foto(str(voluntary.photo)):
                    voluntary.photo.delete()
            voluntary.photo = photo

        voluntary.save()
        messages.success(request, "Membro da comissão atualizado com sucesso!")

    # ── criar ─────────────────────────────────────────────────────────────────
    elif 'name' in request.POST:
        name = request.POST.get('name')
        registration = request.POST.get('registration')

        if not request.POST.get('type_voluntary'):
            messages.error(request, "Informe a função do membro.")
            return redirect(redirect_url)

        type_voluntary = request.POST.get('type_voluntary')
        photo = request.FILES.get('photo')

        if photo:
            err = type_file(request, ['.png', '.jpg', '.jpeg'], photo,
                            'A foto deve ser PNG, JPG ou JPEG.')
            if err:
                return redirect(redirect_url)

        # resolve evento e admin conforme tipo de usuário
        if user.is_staff:
            event = Event.objects.get(id=request.POST.get('event'))
            admin = User.objects.get(id=request.POST.get('user'))
        elif user.type == 1:
            event = user.event_user
            admin = user
        else:
            # type=2
            event = user.event_user
            admin = user

        # resolve unidade
        if user.type == 2:
            # usuário comum: sempre a sua própria unidade
            unit = user.unit
        else:
            # admin e coordenador: unidade enviada no form (opcional)
            unit_id = request.POST.get('unit')
            unit = get_object_or_404(Event_unit, id=unit_id) if unit_id else None

        Voluntary.objects.create(
            type_voluntary=type_voluntary,
            name=name,
            registration=registration,
            admin=admin,
            photo=photo,
            event=event,
            unit=unit,
        )
        messages.success(request, "Membro da comissão técnica cadastrado com sucesso!")

    return redirect(redirect_url)
