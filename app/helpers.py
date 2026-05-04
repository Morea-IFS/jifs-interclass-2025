"""
Funções utilitárias e helpers compartilhados entre as views.
Inclui helpers de verificação de acesso (IDOR), gênero e utilidades gerais.
"""

import logging
import os
import random

from datetime import date

from django.contrib import messages
from django.contrib.auth import get_user_model

from .models import (
    Authenticity,
    Player_team_sport,
)

logger = logging.getLogger(__name__)
User = get_user_model()

# ─── Constantes ──────────────────────────────────────────────────────────────

SEXO_NAMES = {0: "masculino", 1: "feminino", 2: "misto"}

ALPHANUMERIC_CHARS = [
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
    "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
    "U", "V", "W", "X", "Y", "Z",
]


# ─── Helpers de verificação de acesso (IDOR) ─────────────────────────────────

def acesso_evento(user, evento):
    """type 0 / superuser: livre | type 1 e 2: apenas o próprio evento."""
    if user.type == 0 or user.is_superuser:
        return True
    return getattr(user, 'event_user', None) == evento


def acesso_team(user, team):
    """type 0: livre | type 1: evento | type 2: apenas o próprio time."""
    if user.type == 0 or user.is_superuser:
        return True
    if user.type == 1:
        return getattr(user, 'event_user', None) == team.event
    if user.type == 2:
        return getattr(user, 'team', None) == team
    return False


def acesso_team_sport(user, team_sport):
    """Delega para acesso_team usando o time do team_sport."""
    return acesso_team(user, team_sport.team)


def acesso_player(user, player):
    """type 0: livre | type 1: mesmo evento | type 2: mesmo evento e admin."""
    if user.type == 0 or user.is_superuser:
        return True
    if user.type == 1:
        return getattr(user, 'event_user', None) == player.event
    if user.type == 2:
        return (getattr(user, 'event_user', None) == player.event
                and player.admin == user)
    return False


def acesso_match(user, match):
    """type 0: livre | type 1 e 2: mesmo evento."""
    if user.type == 0 or user.is_superuser:
        return True
    return getattr(user, 'event_user', None) == match.event


# ─── Helpers de gênero ───────────────────────────────────────────────────────

def check_gender_compatibility(player, team_sport, user):
    """
    Verifica se o jogador pode entrar no team_sport.
    Retorna (ok: bool, erro: str | None).
    Superusuários passam direto.
    """
    if user.is_superuser:
        return True, None

    team_sexo = team_sport.sexo  # 0 masc | 1 fem | 2 misto

    # time misto aceita qualquer sexo
    if team_sexo == 2:
        return True, None

    # se o jogador já tem sexo definido, ele deve bater com o time
    if player.sexo is not None and player.sexo != team_sexo:
        return False, (
            f"O atleta '{player.name}' é do sexo "
            f"{SEXO_NAMES.get(player.sexo, '?')} e não pode ser adicionado "
            f"a um time {SEXO_NAMES.get(team_sexo, '?')}."
        )

    # verifica vínculos existentes: se o jogador já está num time
    # de sexo diferente (e não misto), bloqueia
    conflito = (
        Player_team_sport.objects
        .filter(player=player)
        .exclude(team_sport=team_sport)
        .exclude(team_sport__sexo=2)          # ignora times mistos
        .exclude(team_sport__sexo=team_sexo)  # ignora times do mesmo sexo
        .select_related("team_sport__team")
        .first()
    )
    if conflito:
        return False, (
            f"O atleta '{player.name}' já participa do time "
            f"'{conflito.team_sport.team.name}' "
            f"({SEXO_NAMES.get(conflito.team_sport.sexo, '?')}) "
            f"e não pode entrar num time {SEXO_NAMES.get(team_sexo, '?')}."
        )

    return True, None


def player_queryset_for_team(team_sport, user, event, admin_user=None):
    """
    Retorna queryset de Player compatível com o sexo do team_sport.
    admin_user restringe por quem cadastrou (para tipo 2).
    """
    from .models import Player
    qs = Player.objects.filter(event=event)

    if admin_user:
        qs = qs.filter(admin=admin_user)

    sexo = team_sport.sexo
    if sexo in (0, 1) and not user.is_superuser:
        # exclui jogadores com sexo INCOMPATÍVEL (nulo é permitido ainda)
        qs = qs.exclude(sexo__in=[s for s in (0, 1) if s != sexo])
        # exclui jogadores já vinculados a times de sexo oposto
        qs = qs.exclude(
            player_team_sport__team_sport__sexo__in=[s for s in (0, 1) if s != sexo]
        )

    return qs.distinct()


# ─── Utilidades gerais ───────────────────────────────────────────────────────

def verificar_foto(url_name):
    """Verifica se a foto NÃO é uma foto padrão do sistema (retorna True se pode deletar)."""
    defaults = ['person.png', 'team.png']
    url_parts = url_name.split('/')
    filename = url_parts[-1]
    return filename not in defaults


def type_file(request, allowed_extensions, file, error_text):
    """
    Verifica se a extensão do arquivo está na lista permitida.
    Retorna True se o arquivo é INVÁLIDO (e adiciona mensagem de erro).
    Retorna False se é válido.
    """
    ext = os.path.splitext(file.name)[1].lower().strip()
    if ext not in allowed_extensions:
        messages.error(request, error_text)
        return True
    return False


def calcular_idade(data_nasc):
    """Calcula idade a partir da data de nascimento."""
    if not data_nasc:
        return 0
    hoje = date.today()
    return hoje.year - data_nasc.year


def generate_authenticity(name, event):
    """Gera um código de autenticidade aleatório para documentos."""
    parts = []
    for i in range(4):
        number = random.randint(1, 8)
        chars = ''.join(random.sample(ALPHANUMERIC_CHARS, number))
        parts.append(chars)
        if i == 3:
            parts.append(f"-{number}")
        else:
            parts.append(f"-{number}-")
    result = str(''.join(parts))
    number = str(random.randint(1111111, 9999999))
    authenticity = Authenticity.objects.create(
        name=name, event=event, code=result, number=number
    )
    return authenticity
