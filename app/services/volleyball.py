"""Lógica de volleyball - swap de times por sets par/ímpar."""

from app.models import Team_match


def get_ordered_team_matches(match):
    """
    Retorna (team_match_a, team_match_b) respeitando swap por set par/ímpar.
    Em partidas de volley, os times trocam de lado a cada set.
    """
    team_matchs = Team_match.objects.filter(match=match)
    if len(team_matchs) < 2:
        return None, None

    if match.volley_match:
        total_sets = (
            match.volley_match.sets_team_a + match.volley_match.sets_team_b
        )
        if total_sets % 2 == 0:
            return team_matchs[0], team_matchs[1]
        else:
            return team_matchs[1], team_matchs[0]

    return team_matchs[0], team_matchs[1]


def get_ordered_sets(match, team_match_a, team_match_b):
    """
    Retorna (sets_a, sets_b) na ordem correta considerando swap.
    """
    if not match.volley_match:
        return 0, 0

    total_sets = (
        match.volley_match.sets_team_a + match.volley_match.sets_team_b
    )
    if total_sets % 2 == 0:
        return match.volley_match.sets_team_a, match.volley_match.sets_team_b
    else:
        return match.volley_match.sets_team_b, match.volley_match.sets_team_a
