# app/signals.py
from django.db.models.signals import post_save, post_delete, pre_delete, post_migrate
from django.dispatch import receiver
from django.conf import settings
from django.templatetags.static import static
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import Group, Permission
from .generators import generate_timer
from django.contrib.auth import get_user_model
from .models import Point, Match, Team_match, Team, Penalties, Volley_match, Player_match, Time_pause, Banner, Player_team_sport, UserSession
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.sessions.models import Session
from django.utils import timezone

User = get_user_model()
default_photo_url = f"{settings.MEDIA_URL}defaults/team.png"

def serialize_players(players_qs):
    result = []
    for pm in players_qs:
        player = pm.player
        result.append({
            "name": player.name,
            "photo_url": player.photo.url if player.photo else default_photo_url,
            "number": getattr(pm, 'player_number', None),
        })
    return result

def generate_score_data():
    if Volley_match.objects.filter(status=1).exists():
        volley_match = Volley_match.objects.get(status=1)
        if Match.objects.filter(volley_match=volley_match, status=1).exists():
            volley_match = Volley_match.objects.get(status=1)
            if Match.objects.filter(volley_match=volley_match).count() > 1:
                match = Match.objects.filter(volley_match=volley_match, status=1).last()
            else:
                match = Match.objects.get(volley_match=volley_match, status=1)

            team_matchs = Team_match.objects.filter(match=match)
            if len(team_matchs) < 2:
                match.status = 3
                match.save()
                return None

            team_match_a = team_matchs[0]
            team_match_b = team_matchs[1]

            if (match.volley_match.sets_team_a + match.volley_match.sets_team_b) % 2 == 0:
                # par
                sets_1 = match.volley_match.sets_team_a
                sets_2 = match.volley_match.sets_team_b
                team_1 = team_match_a
                team_2 = team_match_b
                point_1 = Point.objects.filter(team_match=team_match_a).count()
                point_2 = Point.objects.filter(team_match=team_match_b).count()
                aces_1 = Point.objects.filter(point_types=2, team_match=team_match_a).count()
                aces_2 = Point.objects.filter(point_types=2, team_match=team_match_b).count()
                lack_1 = Penalties.objects.filter(type_penalties=2, team_match=team_match_a).count()
                lack_2 = Penalties.objects.filter(type_penalties=2, team_match=team_match_b).count()
                card_1 = Penalties.objects.filter(type_penalties=0,team_match=team_match_a).count() + Penalties.objects.filter(type_penalties=1,team_match=team_match_a).count()
                card_2 = Penalties.objects.filter(type_penalties=0,team_match=team_match_b).count() + Penalties.objects.filter(type_penalties=1,team_match=team_match_b).count()
            else:
                # impar
                sets_1 = match.volley_match.sets_team_b
                sets_2 = match.volley_match.sets_team_a
                team_1 = team_match_b
                team_2 = team_match_a
                point_1 = Point.objects.filter(team_match=team_match_b).count()
                point_2 = Point.objects.filter(team_match=team_match_a).count()
                aces_1 = Point.objects.filter(point_types=2, team_match=team_match_b).count()
                aces_2 = Point.objects.filter(point_types=2, team_match=team_match_a).count()
                lack_1 = Penalties.objects.filter(type_penalties=2, team_match=team_match_b).count()
                lack_2 = Penalties.objects.filter(type_penalties=2, team_match=team_match_a).count()
                card_1 = Penalties.objects.filter(type_penalties=0,team_match=team_match_a).count() + Penalties.objects.filter(type_penalties=1,team_match=team_match_a).count()
                card_2 = Penalties.objects.filter(type_penalties=0,team_match=team_match_b).count() + Penalties.objects.filter(type_penalties=1,team_match=team_match_b).count()

            point_a = Point.objects.filter(point_types=1, team_match=team_match_a).count()
            point_b = Point.objects.filter(point_types=1, team_match=team_match_b).count()
            aces_a = Point.objects.filter(point_types=2, team_match=team_match_a).count()
            aces_b = Point.objects.filter(point_types=2, team_match=team_match_b).count()

            players_a_qs = Player_match.objects.filter(team_match=team_1)
            players_b_qs = Player_match.objects.filter(team_match=team_2)
            players_a = serialize_players(players_a_qs)
            players_b = serialize_players(players_b_qs)

            if Banner.objects.filter(status=0).exists(): 
                banner_score = Banner.objects.get(status=0).image.url
                banner_status_score = True
            else: 
                banner_score = static('images/logo-jifs-intercampi.svg')
                banner_status_score = False

            name_scoreboard = 'Sets'
            ball_sport = static('images/ball-of-volley.png')

            if match.sexo == 1: 
                img_sexo = static('images/icon-female.svg')
                sexo_color = '#ff32aa' 
            else: 
                img_sexo = static('images/icon-male.svg')
                sexo_color = '#3a7bd5'

            match_data = {
                'agua': "agua",
                'team_a': team_1.team.name,
                'team_b': team_2.team.name,
                'team_a_score': team_match_a.team.name,
                'team_b_score': team_match_b.team.name,
                'sets_a': sets_1,
                'sets_b': sets_2,
                'players_a': players_a,
                'players_b': players_b,
                'teamAcolor': '#02007a',
                'teamBcolor': '#d10000',
                'points_a_score': point_a,
                'points_b_score': point_b,
                'banner_score': banner_score,
                'banner_status_score': banner_status_score,
                'points_a': point_1,
                'points_b': point_2,
                'lack_a': lack_1,
                'lack_b': lack_2,
                'img_sexo': img_sexo,
                'sexo_color': sexo_color,
                'ball_sport': ball_sport,
                'aces_or_card': "Aces",
                'aces_or_card_a': aces_1,
                'aces_or_card_b': aces_2,
                'card_a': card_1,
                'card_b': card_2,
                'aces_a_score': aces_a,
                'aces_b_score': aces_b,
                'sexo_text': match.get_sexo_display(),
                'name_scoreboard': name_scoreboard,
                'photoA': team_1.team.photo.url if team_1.team.photo else default_photo_url,
                'photoB': team_2.team.photo.url if team_2.team.photo else default_photo_url,
                'sets_time_auto': False,
            }
            print("sets on: ", match_data)
            return match_data

    elif Match.objects.filter(status=1).exists():
        match = Match.objects.get(status=1)
        team_matchs = Team_match.objects.filter(match=match)
        if len(team_matchs) < 2:
            return None
        team_match_a = team_matchs[0]
        team_match_b = team_matchs[1]

        point_a = Point.objects.filter(team_match=team_match_a).count()
        point_b = Point.objects.filter(team_match=team_match_b).count()
        lack_a = Penalties.objects.filter(type_penalties=2, team_match=team_match_a).count()
        lack_b = Penalties.objects.filter(type_penalties=2, team_match=team_match_b).count()
        card_a = Penalties.objects.filter(type_penalties=0, team_match=team_match_a).count() + Penalties.objects.filter(type_penalties=1, team_match=team_match_a).count()
        card_b = Penalties.objects.filter(type_penalties=0, team_match=team_match_b).count() + Penalties.objects.filter(type_penalties=1, team_match=team_match_b).count()

        players_a_qs = Player_match.objects.filter(team_match=team_match_a)
        players_b_qs = Player_match.objects.filter(team_match=team_match_b)
        players_a = serialize_players(players_a_qs)
        players_b = serialize_players(players_b_qs)

        seconds, status = generate_timer(match)

        if Banner.objects.filter(status=0).exists(): 
            banner_score = Banner.objects.get(status=0).image.url
            banner_status_score = True
        else: 
            banner_score = static('images/logo-jifs-intercampi.svg')
            banner_status_score = False

        if match.sexo == 1: 
            img_sexo = static('images/icon-female.svg')
            sexo_color = '#ff32aa' 
        else: 
            img_sexo = static('images/icon-male.svg')
            sexo_color = '#3a7bd5'

        if match.sport == 3:
            ball_sport = static('images/ball-of-handball.png')
        else:
            ball_sport = static('images/ball-of-futsal.png')

        name_scoreboard = 'Tempo'

        match_data = {
            'team_a': team_match_a.team.name,
            'team_b': team_match_b.team.name,
            'team_a_score': team_match_a.team.name,
            'team_b_score': team_match_b.team.name,
            'teamAcolor': '#02007a',
            'teamBcolor': '#d10000',
            'points_a': point_a,
            'points_b': point_b,
            'lack_a': lack_a,
            'lack_b': lack_b,
            'sets_a': "00:00",
            'sets_b': 0,
            'card_a': card_a,
            'card_b': card_b,
            'players_a': players_a,
            'players_b': players_b,
            'banner_score': banner_score,
            'banner_status_score': banner_status_score,
            'points_a_score': point_a,
            'points_b_score': point_b,
            'aces_or_card': "Cartões",
            'aces_or_card_a': card_a,
            'aces_or_card_b': card_b,
            'img_sexo': img_sexo,
            'sexo_color': sexo_color,
            'sexo_text': match.get_sexo_display(),
            'ball_sport': ball_sport,
            'name_scoreboard': name_scoreboard,
            'photoA': team_match_a.team.photo.url if team_match_a.team.photo else default_photo_url,
            'photoB': team_match_b.team.photo.url if team_match_b.team.photo else default_photo_url,
            'seconds': seconds,
            'status': status,
            'sets_time_auto': True,
        }
        print(match_data)
        return match_data
    else:
        if Banner.objects.filter(status=0).exists(): 
            banner_score = Banner.objects.get(status=0).image.url
            banner_status_score = True
        else: 
            banner_score = static('images/logo-jifs-intercampi.svg')
            banner_status_score = False
        match_data = {
            'team_a': "TIME A",
            'team_b': "TIME B",
            'points_a': 0,
            'points_b': 0,
            'aces_or_card': "Cartões",
            'aces_or_card_a': 0,
            'aces_or_card_b': 0,
            'teamAcolor': '#02007a',
            'teamBcolor': '#d10000',
            'lack_a': 0,
            'lack_b': 0,
            'sets_a': "00:00",
            'sets_b': 0,
            'card_a': 0,
            'card_b': 0,
            'name_scoreboard': "PLACAR",
            'photoA': default_photo_url,
            'photoB': default_photo_url,
            'banner_score': banner_score,
            'banner_status_score': banner_status_score,
        }
        return match_data
    
def send_score_update():
    channel_layer = get_channel_layer()
    match_data = generate_score_data()
    async_to_sync(channel_layer.group_send)(
        'placar',
        {
            'type': 'match_update',
            'match': match_data,
        }
    )

@receiver([post_save, post_delete], sender=Team)
def team_updated(sender, instance, using, **kwargs):
    if settings.DEBUG: print("hmm, mudanças nos times :)")
    send_score_update()


@receiver([post_save, post_delete], sender=Volley_match)
def volley_updated(sender, instance, using, **kwargs):
    if settings.DEBUG: print("hmm, mudanças nas partidas de vôlei :)")
    send_score_update()

@receiver([post_save, post_delete], sender=Point)
def point_changed(sender, instance, using, **kwargs):
    if settings.DEBUG: print("hmm, mudanças nos pontos :)")
    channel_layer = get_channel_layer()
    match_data = send_scoreboard_point()
    async_to_sync(channel_layer.group_send)(
        'scoreboard',
        {
            'type': 'point_new',
            'match': match_data,
        }
    )

def send_scoreboard_point():
    if settings.DEBUG: print("eita, mudanças (pontos) sendo preparadas. :)")
    if Match.objects.filter(status=1):
        match = Match.objects.get(status=1)
        team_matchs = Team_match.objects.filter(match=match)
        if len(team_matchs) < 2:
            return None
        if match.volley_match:
            if (match.volley_match.sets_team_a + match.volley_match.sets_team_b) % 2 == 0:
                team_match_a = team_matchs[0]
                team_match_b = team_matchs[1]
            else:
                team_match_a = team_matchs[1]
                team_match_b = team_matchs[0]
        else:
            team_match_a = team_matchs[0]
            team_match_b = team_matchs[1]

        point_a = Point.objects.filter(team_match=team_match_a).count()
        point_b = Point.objects.filter(team_match=team_match_b).count()

        match_data = {
            'point_a': point_a,
            'point_b': point_b,
        }
        if match.volley_match:
            match_data['aces_a'] = Point.objects.filter(point_types=2, team_match=team_match_a).count()
            match_data['aces_b'] = Point.objects.filter(point_types=2, team_match=team_match_b).count()
    else:
        match_data = {
            'point_a': 0,
            'point_b': 0,
        }   
    if settings.DEBUG: print("eita, saindo signals (pontos) sendo preparadas. :)")
    if settings.DEBUG: print(match_data)
    return match_data


@receiver([post_save, post_delete], sender=Time_pause)
def point_changed(sender, instance, using, **kwargs):
    if settings.DEBUG: print("hmm, mudanças no (tempo) :)")
    channel_layer = get_channel_layer()
    match_data = send_scoreboard_time()
    async_to_sync(channel_layer.group_send)(
        'scoreboard',
        {
            'type': 'time_new',
            'match': match_data,
        }
    )

def send_scoreboard_time():
    if settings.DEBUG: print("eita, mudanças (tempo) sendo preparadas. :)")
    if Match.objects.filter(status=1):
        match = Match.objects.get(status=1)
        seconds, status = generate_timer(match)

        match_data = {
            'seconds': seconds,
            'status': status,
        }
    if settings.DEBUG: print("eita, saindo signals (tempo) sendo preparadas. :)")
    if settings.DEBUG: print(match_data)
    return match_data

@receiver([post_save, post_delete], sender=Banner)
def banner_changed(sender, instance, using, **kwargs):
    if settings.DEBUG: print("hmm, mudanças nas banner :)")
    channel_layer = get_channel_layer()
    match_data = send_scoreboard_banner()
    async_to_sync(channel_layer.group_send)(
        'scoreboard',
        {
            'type': 'banner_new',
            'match': match_data,
        }
    )

def send_scoreboard_banner():
    if settings.DEBUG: print("eita, mudanças (banner) sendo preparadas. :)")
    match_data = {}
    if Banner.objects.filter(status=0).exists(): 
        match_data['status'] = 1
        match_data['banner'] = Banner.objects.filter(status=0)[0].image.url
    else:
        match_data['status'] = 0
    if settings.DEBUG: print("eita, saindo signals (banner) sendo preparadas. :)")
    if settings.DEBUG: print(match_data)
    return match_data

@receiver([post_save, post_delete], sender=Penalties)
def penalties_updated(sender, instance, using, **kwargs):
    if settings.DEBUG: print("hmm, mudanças nas penalidades :)")
    channel_layer = get_channel_layer()
    match_data = send_scoreboard_penalties(instance)
    async_to_sync(channel_layer.group_send)(
        'scoreboard',
        {
            'type': 'penalties_new',
            'match': match_data,
        }
    )

def send_scoreboard_penalties(instance):
    if settings.DEBUG: print("eita, mudanças (penalidades) sendo preparadas. :)")
    if Match.objects.filter(status=1):
        match = Match.objects.get(status=1)
        team_matchs = Team_match.objects.filter(match=match)
        if len(team_matchs) < 2:
            return None
        if match.volley_match:
            if (match.volley_match.sets_team_a + match.volley_match.sets_team_b) % 2 == 0:
                team_match_a = team_matchs[0]
                team_match_b = team_matchs[1]
            else:
                team_match_a = team_matchs[1]
                team_match_b = team_matchs[0]
        else:
            team_match_a = team_matchs[0]
            team_match_b = team_matchs[1]

        lack_a = Penalties.objects.filter(type_penalties=2, team_match=team_match_a).count()
        lack_b = Penalties.objects.filter(type_penalties=2, team_match=team_match_b).count()
        card_a = Penalties.objects.filter(type_penalties=0, team_match=team_match_a).count() + Penalties.objects.filter(type_penalties=1, team_match=team_match_a).count()
        card_b = Penalties.objects.filter(type_penalties=0, team_match=team_match_b).count() + Penalties.objects.filter(type_penalties=1, team_match=team_match_b).count()

        match_data = {
            'lack_a': lack_a,
            'lack_b': lack_b,
            'card_a': card_a,
            'card_b': card_b,
        }
        if instance.player:
            print(instance.type_penalties)
            match_data['penalties_player'] = instance.player.name
            if instance.type_penalties == '0': match_data['penalties_url'] = static('images/card-red.png')
            elif instance.type_penalties == '1': match_data['penalties_url'] = static('images/card-yellow.png')
            else: match_data['penalties_url'] = static('images/whistle.png')
    else:
        match_data = {
            'lack_a': 0,
            'lack_b': 0,
            'card_a': 0,
            'card_b': 0,
        }   
    if settings.DEBUG: print("eita, saindo signals (penalidades) sendo preparadas. :)")
    if settings.DEBUG: print(match_data)
    return match_data

@receiver([post_save, post_delete], sender=Match)
def match_updated(sender, instance, using, **kwargs):
    if settings.DEBUG: print("hmm, mudanças nas partidas :)")
    channel_layer = get_channel_layer()
    match_data, match_public = send_scoreboard_match()
    async_to_sync(channel_layer.group_send)(
        'scoreboard',
        {
            'type': 'match_new',
            'match': match_data,
        }
    )
    async_to_sync(channel_layer.group_send)(
        'public',
        {
            'type': 'match_new',
            'match': match_public,
        }
    )

def send_scoreboard_match():
    if settings.DEBUG: print("eita, mudanças (partidas) sendo preparadas. :)")
    match = None
    if Volley_match.objects.filter(status=1).exists():
        volley_match = Volley_match.objects.get(status=1)
        if Match.objects.filter(volley_match=volley_match, status=1).exists():
            match = Match.objects.get(volley_match=volley_match, status=1)
    elif Match.objects.filter(status=1):
        match = Match.objects.get(status=1)
        seconds, status = generate_timer(match)
    if match:
        team_matchs = Team_match.objects.filter(match=match)
        if len(team_matchs) < 2:
            return None

        if match.volley_match:
            if (match.volley_match.sets_team_a + match.volley_match.sets_team_b) % 2 == 0:
                team_match_a = team_matchs[0]
                team_match_b = team_matchs[1]
                sets_a = match.volley_match.sets_team_a
                sets_b = match.volley_match.sets_team_b
            else:
                team_match_a = team_matchs[1]
                team_match_b = team_matchs[0]
                sets_b = match.volley_match.sets_team_a
                sets_a = match.volley_match.sets_team_b
            ball_sport = static('images/ball-of-volley.png')
        else:
            team_match_a = team_matchs[0]
            team_match_b = team_matchs[1]
            if match.sport == 3: ball_sport = static('images/ball-of-handball.png')
            else: ball_sport = static('images/ball-of-futsal.png')

        point_a = Point.objects.filter(team_match=team_match_a).count()
        point_b = Point.objects.filter(team_match=team_match_b).count()
        lack_a = Penalties.objects.filter(type_penalties=2, team_match=team_match_a).count()
        lack_b = Penalties.objects.filter(type_penalties=2, team_match=team_match_b).count()
        card_a = Penalties.objects.filter(type_penalties=0, team_match=team_match_a).count() + Penalties.objects.filter(type_penalties=1, team_match=team_match_a).count()
        card_b = Penalties.objects.filter(type_penalties=0, team_match=team_match_b).count() + Penalties.objects.filter(type_penalties=1, team_match=team_match_b).count()

        match_data = {
            'team_name_a': team_match_a.team.name,
            'team_name_b': team_match_b.team.name,
            'match_sexo': match.get_sexo_display(),
            'match_sport': match.get_sport_display(),
            'point_a': point_a,
            'ball_sport': ball_sport,
            'point_b': point_b,
            'lack_a': lack_a,
            'lack_b': lack_b,
            'card_a': card_a,
            'card_b': card_b,
            'photoA': team_match_a.team.photo.url if team_match_a.team.photo else default_photo_url,
            'photoB': team_match_b.team.photo.url if team_match_b.team.photo else default_photo_url,
        }

        if match.volley_match:
            match_data['sets_a'] = sets_a
            match_data['sets_b'] = sets_b
            match_data['aces_a'] = Point.objects.filter(point_types=2, team_match=team_match_a).count()
            match_data['aces_b'] = Point.objects.filter(point_types=2, team_match=team_match_b).count()
        else:
            match_data['seconds'] = seconds
            match_data['status'] = status

        players_a_qs = Player_match.objects.filter(team_match=team_match_a)
        players_b_qs = Player_match.objects.filter(team_match=team_match_b)

        match_public = match_data

        match_public['players_a'] = serialize_players(players_a_qs)
        match_public['players_b'] = serialize_players(players_b_qs)
        
    else:
        match_data = {
            'team_name_a': "TEAM A",
            'team_name_b': "TEAM B",
            'match_sexo': "Nenhum",
            'match_sport': "Nenhum",
            'point_a': 0,
            'point_b': 0,
            'lack_a': 0,
            'lack_b': 0,
            'card_a': 0,
            'card_b': 0,
            'photoA': default_photo_url,
            'photoB': default_photo_url,
        }   

        match_public = match_data

    if settings.DEBUG: print("eita, saindo signals (partidas) sendo preparadas. :)")
    if settings.DEBUG: print(match_data)
    return match_data, match_public

@receiver(post_save, sender=User)
def set_type_for_staff(sender, instance, created, **kwargs):
    if settings.DEBUG: print("chegouuu")
    if created and instance.is_staff:
        instance.type = 0
        instance.save()
    elif int(instance.type) == 1:
        group_name = "event coordinator"
        group, _ = Group.objects.get_or_create(name=group_name)
        instance.groups.add(group)
    elif int(instance.type) == 2:
        group_name = "user common"
        group, _ = Group.objects.get_or_create(name=group_name)
        instance.groups.add(group)
    elif int(instance.type) == 3:
        group_name = "score marker"
        group, _ = Group.objects.get_or_create(name=group_name)
        instance.groups.add(group)
    else:
        if settings.DEBUG: print(instance.type, " - ", type(instance.type), " - ", type(int(instance.type)))

@receiver(post_migrate)
def create_user_common_group(sender, **kwargs):
    if sender.name != "app":  
        return

    group_name = "event coordinator"
    group, created = Group.objects.get_or_create(name=group_name)

    # Lista de permissões que você quer adicionar
    permission_codenames = [
        "view_attachments",
        "view_event_sport",
        "view_help",

        "view_match",
        "view_team",
        "view_event",

        "add_player",
        "change_player",
        "delete_player",
        "view_player",

        "add_customuser",
        "change_customuser",
        "delete_customuser",
        "view_customuser",

        "add_player_team_sport",
        "change_player_team_sport",
        "delete_player_team_sport",
        "view_player_team_sport",

        "add_team_sport",
        "change_team_sport",
        "delete_team_sport",
        "view_team_sport",
        
        "add_voluntary",
        "change_voluntary",
        "delete_voluntary",
        "view_voluntary",

        "add_point",
        "add_assistance",
        
    ]

    permissions = Permission.objects.filter(codename__in=permission_codenames)

    if permissions.exists():
        group.permissions.set(permissions)
        if settings.DEBUG: print(f"✅ Grupo '{group_name}' criado/atualizado com permissões.")
    else:
        if settings.DEBUG: print("⚠️ Nenhuma permissão encontrada. Verifique os codenames.")


    group_name = "user common"
    group, created = Group.objects.get_or_create(name=group_name)

    # Lista de permissões que você quer adicionar
    permission_codenames = [
        "view_attachments",
        "view_event_sport",
        "view_help",
        "view_match",

        "add_player",
        "change_player",
        "delete_player",
        "view_player",

        "add_player_team_sport",
        "change_player_team_sport",
        "delete_player_team_sport",
        "view_player_team_sport",

        "add_team_sport",
        "change_team_sport",
        "delete_team_sport",
        "view_team_sport",

    ]

    permissions = Permission.objects.filter(codename__in=permission_codenames)

    if permissions.exists():
        group.permissions.set(permissions)
        if settings.DEBUG: print(f"✅ Grupo '{group_name}' criado/atualizado com permissões.")
    else:
        if settings.DEBUG: print("⚠️ Nenhuma permissão encontrada. Verifique os codenames.")


    group_name = "score marker"
    group, created = Group.objects.get_or_create(name=group_name)

    # Lista de permissões que você quer adicionar
    permission_codenames = [
        "view_volley_match",
        "view_match",

        "add_point",
        "add_assistance",

    ]

    permissions = Permission.objects.filter(codename__in=permission_codenames)

    if permissions.exists():
        group.permissions.set(permissions)
        if settings.DEBUG: print(f"✅ Grupo '{group_name}' criado/atualizado com permissões.")
    else:
        if settings.DEBUG: print("⚠️ Nenhuma permissão encontrada. Verifique os codenames.")

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")

@user_logged_in.connect
def on_user_logged_in(sender, request, user, **kwargs):
    session_key = request.session.session_key
    session = Session.objects.get(session_key=session_key)
    ip = get_client_ip(request)
    device = request.user_agent.device.family
    browser = request.user_agent.browser.family
    os = request.user_agent.os.family


    UserSession.objects.update_or_create(
        session=session,
        defaults={
            "user": user,
            "ip_address": ip,
            "device": device,
            "browser": browser,
            "os": os,
            "last_activity": timezone.now(),
        }
    )

@user_logged_out.connect
def on_user_logged_out(sender, request, user, **kwargs):
    try:
        UserSession.objects.filter(session__session_key=request.session.session_key).delete()
    except:
        pass
