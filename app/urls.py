from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from . import views

urlpatterns = [
    path('<int:event_id>' , views.home_public, name = "home_public"),
    path('placar/<int:event_id>' , views.scoreboard_public, name="scoreboard_public"),
    path('scoreboard_projector/<int:event_id>', views.scoreboard_projector, name="scoreboard_projector"),
    path('sobre/<int:event_id>', views.about_us, name="about_us"),
    path('login' , views.login, name = "login"),
    path('' , views.events_list, name = "events"),
    path('logout', views.sair, name='logout'),
    path('morea-admin', views.home_admin, name = "Home"),
    path('manage/player', views.player_manage, name = "player_manage"),
    path('edit/player/<int:id>', views.player_edit, name = "player_edit"),
    path('manage/team', views.team_manage, name = "team_manage"),
    path('edit/team/<int:id>', views.team_edit, name = "team_edit"),
    path('manage/team/player/<int:id>', views.team_players_manage, name = "team_players_manage"),
    path('edit/player/<int:id>/team/<int:team>', views.team_players_edit, name = "team_player_edit"),
    path('manage/match', views.matches_manage, name = "matches_manage"),
    path('edit/match/<int:id>', views.matches_edit, name = "matches_edit"),
    path('add/player/team/<int:id>', views.add_player_team, name = "add_player_team"),
    path('games', views.games, name = "games"),
    path('attachments', views.attachments, name = "attachments"),
    path('manage/user', views.user_manage, name = "user_manage"),
    path('manage/voluntary', views.voluntary_manage, name = "voluntary_manage"),
    path('scoreboard/<int:event_id>', views.scoreboard, name = "scoreboard"),
    path('manage/banner', views.banner_manage, name="banner_manage"),
    path('register/banner', views.banner_register, name="banner_register"),
    path('players_match/<int:id>', views.players_match, name = "players_match"),
    path('players_in_teams/<int:id>', views.players_in_teams, name = "players_in_teams"),
    path('upload', views.upload_document, name='upload_document'),
    path('dados', views.boss_data, name='boss_data'),
    path('termos', views.terms_use, name='terms_use'),
    path('erro404', views.page_in_erro404),
    path('settings', views.settings, name="settings"),
    path('settings_new', views.settings_new, name="settings_new"),
    path("status/", views.manage_session, name="manage_sessions"),
    path("match/<int:id_sport>/<int:id_match>", views.match_settings, name="match_settings"),

    path('manage/statement', views.statement_manage, name="statement_manage"),
    path('register/statement', views.statement_register, name="statement_register"),
    path('chefe_manage', views.chefe_manage, name="chefe_manage"),
    path('theme', views.theme_manage, name="theme"),
    path('faq_manage', views.faq_manage, name="faq_manage"),
    path('faq_register', views.faq_register, name="faq_register"),
    path('enrollment_manage', views.enrollment_manage, name="enrollment_manage"),
    path('enrollment_register', views.enrollment_register, name="enrollment_register"),
    path('anexo_manage', views.anexo_manage, name="anexo_manage"),
    path('anexo_register', views.anexo_register, name="anexo_register"),

    path('manage/event', views.event_manage, name="event_manage"),
    path('manage/sport', views.event_sport_manage, name="event_sport_manage"),
    path('edit/sport', views.event_sport_edit, name="event_sport_edit"),

    path('register_team/<int:event_id>', views.register_team, name="guiate_register_team"),
    path('team/<str:sport_name>/<int:event_id>', views.team_sexo, name="guiate_team"),
    path('players/<str:team_name>/<str:team_sexo>/<str:sport_name>/<int:event_id>', views.players_team, name="guiate_players_team"),
    path('players/<str:team_name>/list/<str:team_sexo>/<str:sport_name>', views.players_list, name="guiate_players_list"),
    path('players/<str:team_name>/edit/<int:id>/<str:team_sexo>/<str:sport_name>', views.player_list_edit, name = "player_list_edit"),

    path('dashboard', views.dashboard, name="dashboard"),

    path('generator/badge', views.generator_badge, name="badge"),
    path('generator/certificate', views.generator_certificate, name="certificate"),
    path('generator/data', views.generator_data, name="data"),

    #API
    path('get_teams/', views.get_teams, name='get_teams'),
    path('get_sexos/', views.get_sexos, name='get_sexos'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    


