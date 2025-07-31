from functools import wraps
from django.shortcuts import redirect
from datetime import datetime
import pytz
from .models import Event, Terms_Use
from django.contrib import messages

def time_restriction(redirect_page="Home"):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.type == 0 or request.user.type == 1 or request.user.is_staff:
                return view_func(request, *args, **kwargs)
            else:
                print("uaieo")
                brasilia_tz = pytz.timezone('America/Sao_Paulo')
                now = datetime.now(brasilia_tz)
                
                config = Event.objects.get(id=request.user.event_user.id)

                if config.enrollment_init and config.enrollment_end:
                    if config.enrollment_init.tzinfo is None:
                        config.enrollment_init = brasilia_tz.localize(config.enrollment_init)

                    if not config or (config.enrollment_init <= now <= config.enrollment_end):
                        print("vaaai")
                        return view_func(request, *args, **kwargs)
                    else:
                        messages.info(request, "O período para realizar as inscrições e edições já foi finalizado.")
                        return redirect(redirect_page)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def terms_accept_required(view_func):
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        try:
            termo = Terms_Use.objects.get(usuario=request.user)

            if not termo.document:
                return redirect('upload_document')

            if not (termo.name and termo.siape):
                return redirect('boss_data')

            if not termo.accepted:
                return redirect('terms_use')

        except Terms_Use.DoesNotExist:
            return redirect('upload_document')

        return view_func(request, *args, **kwargs)
    
    return wrapper