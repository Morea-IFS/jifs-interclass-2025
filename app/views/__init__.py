"""
Pacote views — re-exporta todas as views dos submódulos para
compatibilidade com `from . import views` no urls.py.
"""

# ── errors.py ─────────────────────────────────────────────────────────────────
from app.views.errors import (
    page_in_erro404,
    erro_403_customizado,
    erro_404_customizado,
)

# ── auth.py ───────────────────────────────────────────────────────────────────
from app.views.auth import (
    login,
    sair,
    upload_document,
    boss_data,
    terms_use,
    has_accepted_terms,
)

# ── api.py ────────────────────────────────────────────────────────────────────
from app.views.api import (
    get_teams,
    get_sexos,
    get_groups,
    search_player_preview,
)

# ── players.py ────────────────────────────────────────────────────────────────
from app.views.players import (
    player_manage,
    player_edit,
)

# ── teams.py ──────────────────────────────────────────────────────────────────
from app.views.teams import (
    team_manage,
    team_edit,
    team_players_manage,
    add_player_team,
)

# ── events.py ─────────────────────────────────────────────────────────────────
from app.views.events import (
    event_manage,
    event_sport_manage,
    event_sport_edit,
)

# ── volunteers.py ─────────────────────────────────────────────────────────────
from app.views.volunteers import (
    voluntary_manage,
)

# ── users.py ──────────────────────────────────────────────────────────────────
from app.views.users import (
    user_manage,
    manage_session,
)

# ── public.py ─────────────────────────────────────────────────────────────────
from app.views.public import (
    events_list,
    home_public,
    home_admin,
    switching_public,
    about_us,
    authenticate_file,
)

# ── matches.py ────────────────────────────────────────────────────────────────
from app.views.matches import (
    matches_manage,
    matches_edit,
    games,
    match_settings,
    players_in_teams,
    players_match,
    add_players_match,
)

# ── scoreboard.py ─────────────────────────────────────────────────────────────
from app.views.scoreboard import (
    scoreboard,
    scoreboard_public,
    scoreboard_projector,
)

# ── settings_views.py ─────────────────────────────────────────────────────────
from app.views.settings_views import (
    settings,
    settings_new,
    theme_manage,
    banner_register,
    banner_manage,
    statement_register,
    statement_manage,
    chefe_manage,
    faq_manage,
    faq_register,
    anexo_manage,
    anexo_register,
    enrollment_manage,
    enrollment_register,
    attachments,
)

# ── generators.py ─────────────────────────────────────────────────────────────
from app.views.generators import (
    generator_badge,
    generator_certificate,
    generator_data,
    generator_spreadsheet,
)

# ── dashboard.py ──────────────────────────────────────────────────────────────
from app.views.dashboard import (
    dashboard_acesso,
    dashboard_acesso_user_detail,
)
