from functools import wraps
from django.shortcuts import redirect
from datetime import datetime
import pytz
from .models import Event, Terms_Use
from django.contrib import messages
from django.urls import resolve

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
        print("printe1")
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.is_superuser or request.user.type == 1 or request.user.type == 3:
            return view_func(request, *args, **kwargs)    
        
        if resolve(request.path_info).url_name == 'logout':
            return view_func(request, *args, **kwargs)
        
        if request.user.event_user.general_need_terms:
            if request.user.event_user:
                if request.user.event_user.general_need_authorization:
                    if not request.user.document:
                        return redirect('upload_document')

            if not (request.user.first_name and request.user.telefone and request.user.photo):
                return redirect('boss_data')

            if not request.user.accepted:
                return redirect('terms_use')
        return view_func(request, *args, **kwargs)
    
    return wrapper