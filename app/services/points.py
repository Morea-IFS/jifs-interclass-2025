"""Cálculo de pontos e penalidades para partidas."""

from app.models import Point, Penalties


def calculate_points(team_match, sport):
    """
    Calcula pontos de um team_match considerando o tipo de esporte.
    No futsal (sport=0), subtrai penalidades do total.
    """
    total = Point.objects.filter(team_match=team_match).count()
    if sport == 0:
        penalties_count = Point.objects.filter(
            point_types=2, team_match=team_match
        ).count()
        return total - penalties_count
    return total


def calculate_penalties_count(team_match):
    """
    Retorna dict com contagem de faltas e cartões para um team_match.
    """
    lack = Penalties.objects.filter(
        type_penalties=2, team_match=team_match
    ).count()
    card_red = Penalties.objects.filter(
        type_penalties=0, team_match=team_match
    ).count()
    card_yellow = Penalties.objects.filter(
        type_penalties=1, team_match=team_match
    ).count()
    return {
        'lack': lack,
        'cards': card_red + card_yellow,
        'card_red': card_red,
        'card_yellow': card_yellow,
    }


def get_aces_count(team_match):
    """Retorna contagem de aces (point_types=2) para um team_match."""
    return Point.objects.filter(
        point_types=2, team_match=team_match
    ).count()


def get_penalties_points_count(team_match):
    """Retorna contagem de pontos tipo penalidade (point_types=2)."""
    return Point.objects.filter(
        point_types=2, team_match=team_match
    ).count()
