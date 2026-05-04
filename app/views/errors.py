"""Views de tratamento de erros."""

from django.shortcuts import render, redirect
from django.contrib import messages


def page_in_erro404(request):
    return render(request, 'error_404.html', status=404)


def erro_403_customizado(request, exception=None):
    messages.info(request, "Você não tem permissão para acessar essa página. Contate o administrador.")
    return redirect('Home')


def erro_404_customizado(request, exception):
    return render(request, 'public/error_404.html', status=404)
