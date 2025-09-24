from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.timezone import localtime
from django.utils import timezone
from django.conf import settings

# Create your models here.

# models.py

class Status(models.IntegerChoices):
    shortly = 0, "Em breve"
    happening = 1, "Acontecendo"
    finished = 2, "Finalizada"
    cancelado = 3, "Cancelada"
    paused = 4, "Pausada"
    empty = 5, "Nenhum"

class Sport_types(models.IntegerChoices):
    futsal = 0, "Futsal"
    volleyball = 1, "Voleibol"
    volley_sitting = 2, "Voleibol sentado"
    handball = 3, "Handebol"
    chess = 4, "Xadrez"
    table_tennis = 5, "Tênis de mesa"
    race = 6, "100 M"
    high_jump = 7, "Salto em distância"
    launch_dart = 8, "Lançamento de dardo"
    pitch_weight = 9, "Arremesso de peso"
    discus_throw = 10, "Arremesso de disco"
    burned = 11, "Queimado"

class Campus_types(models.IntegerChoices):
    aracaju = 0, "Aracaju"
    estancia = 1, "Estância"
    gloria = 2, "Glória"
    itabaiana = 3, "Itabaiana"
    lagarto = 4, "Lagarto"
    poco_redondo = 5, "Poço Redondo"
    propria = 6, "Propriá"
    sao_cristovao = 7, "São Cristovão"
    socorro = 8, "Socorro"
    tobias_barreto = 9, "Tobias Barreto"
    reitoria = 10, "Reitoria"

class Users_types(models.IntegerChoices):
    admin = 0, "Administrador"
    manager_event = 1, "Coordenador de evento"
    user_common = 2, "Usuário comum"
    voluntary = 3, "Marcador de pontos"
    
class Point_types(models.IntegerChoices):
    goal = 0, "Gol"
    point = 1, "Ponto"
    ace = 2, "Ace"
    empty = 3, "Nenhum"

class Activity(models.IntegerChoices):
    holder = 0, "Titular"
    reserve = 1, "Reserva"
    empty = 2, "Nenhum"

class Type_penalties(models.IntegerChoices):
    card_red = 0, "Cartão Vermelho"
    card_yellow = 1, "Cartão Amarelo"
    lack = 2, "Falta"
    empty = 3, "Nenhum"

class Events_need(models.IntegerChoices):
    masculine = 0, "Masculino"
    feminine = 1, "Feminino"
    mixed = 2, "Misto"

class Type_Banner(models.IntegerChoices):
    In_use = 0, "Ativo"
    empty = 1, "Inativo"

class Type_service(models.IntegerChoices):
    voluntary = 0, "Voluntário"
    technician = 1, "Técnico de modalidade esportiva"
    organization = 2, "Apoio"
    trainee = 3, "Estagiário"
    head_delegation = 4,"Chefe de delegação"

class Sexo_types(models.IntegerChoices):
    masculine = 0, "Masculino"
    feminine = 1, "Feminino"
    mixed = 2, "Misto"

class UserSession(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name="extra")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device = models.TextField(null=True, blank=True)
    browser = models.TextField(null=True, blank=True)
    os = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.ip_address or 'desconhecido'}"

class Event(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='events/')
    description = models.TextField(blank=True, null=True)
    date_init = models.DateField(blank=True, null=True)
    date_end = models.DateField(blank=True, null=True)
    enrollment_init = models.DateTimeField(blank=True, null=True)
    enrollment_end = models.DateTimeField(blank=True, null=True)
    local = models.CharField(max_length=100, blank=True, null=True)
    active = models.BooleanField(default=True) 
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    regulation = models.FileField(upload_to='events/', blank=True, null=True)
    age = models.IntegerField(default=99)

    player_need_instagram = models.BooleanField(default=True) 
    player_need_photo = models.BooleanField(default=True) 
    player_need_bulletin = models.BooleanField(default=True) 
    player_need_rg = models.BooleanField(default=True) 
    player_need_sexo = models.BooleanField(default=True) 
    player_need_registration = models.BooleanField(default=True) 
    player_need_cpf = models.BooleanField(default=True) 
    player_need_date_nasc = models.BooleanField(default=True) 

    def __str__(self):
        return self.name

class Event_sport(models.Model):
    name = models.CharField(max_length=50 ,null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="sport_set")
    sport = models.IntegerField(choices=Sport_types.choices)
    min_sport = models.PositiveIntegerField(default=1)
    max_sport = models.PositiveIntegerField(default=99)
    fem = models.BooleanField(default=True)
    masc = models.BooleanField(default=True)
    mist = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.event.name} | {self.get_sport_display()}"

class Event_need(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="need_set")

class CustomUser(AbstractUser):
    telefone = models.CharField(max_length=20, blank=True, null=True)
    date_nasc = models.DateField(blank=True, null=True)
    photo = models.ImageField(upload_to='avatars/', blank=True, null=True)
    team = models.ForeignKey('Team', on_delete=models.CASCADE, blank=True, null=True)
    event_user = models.ForeignKey(Event, on_delete=models.CASCADE, blank=True, null=True, related_name="user_set")
    type = models.IntegerField(choices=Users_types.choices, default=3)
    address = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.username

class Settings_access(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField()

    def __str__(self):    
        return f"{self.start} | {self.end}"

class Help(models.Model):
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=500)

    def __str__(self):    
        return f"{self.title} | {self.description}"

class Player(models.Model):
    name = models.CharField(max_length=100)
    instagram = models.CharField(max_length=100, blank=True, null=True)
    classroom = models.CharField(max_length=100, blank=True, null=True)
    photo = models.ImageField(upload_to='photo_player/', default='defaults/person.png', blank=True, null=True)
    bulletin = models.FileField(upload_to='bulletins/', blank=True, null=True)
    rg = models.FileField(upload_to='rg/', blank=True, null=True)
    sexo = models.IntegerField(choices=Sexo_types.choices, blank=True, null=True)
    registration = models.CharField(max_length=15, default="0000000000", blank=True, null=True)
    cpf = models.CharField(max_length=11, default="00000000000", blank=True, null=True)
    date_nasc = models.DateField(default=timezone.now, blank=True, null=True)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):    
        return f"{self.name} | {self.sexo} | {self.admin.username}"
    
class Voluntary(models.Model):
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='photo_voluntary/', default='defaults/person.png', blank=True, null=True)
    registration = models.CharField(max_length=11, default="00000000000", blank=True, null=True)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type_voluntary = models.IntegerField(choices=Type_service.choices, default=Type_service.voluntary)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="voluntary_set")

    def __str__(self):    
        return f"{self.name}"

class Team(models.Model):
    name = models.CharField(max_length=100, blank=True)
    description = models.TextField(max_length=200, blank=True, null=True)
    photo = models.ImageField(upload_to='logo_team/', default='defaults/team.png', blank=True, null=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    status = models.BooleanField(default=True)

    def __str__(self):    
        return f"{self.name}"
    
class Attachments(models.Model):
    name = models.CharField(max_length=100, blank=True)
    file = models.FileField(upload_to='attachments/', blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    public = models.BooleanField(default=False)

    def __str__(self):    
        return f"{self.name} - {self.id}"

class Certificate(models.Model):
    name = models.CharField(max_length=100, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.ImageField(upload_to='certificate/', blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):    
        return f"{self.name}"

class Team_sport(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    sport = models.ForeignKey(Event_sport, on_delete=models.CASCADE)
    sexo = models.IntegerField(choices=Sexo_types.choices)
    status = models.BooleanField(default=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="team_sport_set")

    def __str__(self):      
        return f"{self.team.name} | {self.get_sexo_display()}"
    
class Player_team_sport(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    team_sport = models.ForeignKey(Team_sport, on_delete=models.CASCADE, related_name="players")

    def __str__(self):    
        return f"{self.player} | {self.team_sport}"

class Team_match(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    match = models.ForeignKey('Match', on_delete=models.CASCADE, related_name='teams')

    def __str__(self):    
        return f"{self.team} | {self.match}"

class Volley_match(models.Model):
    status = models.IntegerField(choices=Status.choices, default=Status.empty)
    sets_team_a = models.IntegerField(default=0)
    sets_team_b = models.IntegerField(default=0)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):    
        return f"{self.get_status_display()} | {self.sets_team_a} | {self.sets_team_b}"

class Match(models.Model):
    sport = models.IntegerField(choices=Sport_types.choices)
    status = models.IntegerField(choices=Status.choices, default=Status.shortly)
    time_start = models.TimeField(blank=True, null=True)
    time_end = models.TimeField(blank=True, null=True)
    sexo = models.IntegerField(choices=Sexo_types.choices, default=Sexo_types.mixed, blank=True)
    mvp_player_player = models.ForeignKey(Player, on_delete=models.CASCADE, blank=True, null=True)
    Winner_team = models.ForeignKey(Team, on_delete=models.CASCADE, blank=True, null=True)
    volley_match = models.ForeignKey(Volley_match, on_delete=models.CASCADE, blank=True, null=True, related_name="matches")
    add = models.TimeField(blank=True, null=True)
    time_match = models.DateTimeField(null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):    
        return f"{self.id} | {self.get_sport_display()} | {self.get_status_display()} | {self.sexo}"

class Point(models.Model):
    point_types = models.IntegerField(choices=Point_types.choices, default=Point_types.empty)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True)
    team_match = models.ForeignKey(Team_match, on_delete=models.CASCADE)
    time = models.TimeField(auto_now_add=True)

    def __str__(self):    
        if self.player:
            return f"{self.point_types} | {self.player} | {self.team_match} | {self.time}"
        else:
            return f"{self.point_types} | {self.team_match} | {self.time}"

class Assistance(models.Model):
    assis_to = models.ForeignKey(Point, on_delete=models.CASCADE)
    player = models.ForeignKey('Player_match', on_delete=models.CASCADE)

    def __str__(self):    
        return f"{self.assis_to} | {self.player}"

class Player_match(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    player_number = models.IntegerField(blank=True, null=True, default=0)
    activity = models.IntegerField(choices=Activity.choices, default=Activity.empty)
    team_match = models.ForeignKey(Team_match, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):    
        return f"{self.player} | {self.match} | {self.player_number} | {self.team_match} | {self.get_activity_display()}" 
class Penalties(models.Model):
    type_penalties = models.IntegerField(choices=Type_penalties.choices, default=Type_penalties.empty)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True)
    team_match = models.ForeignKey(Team_match, on_delete=models.CASCADE)
    time = models.TimeField(auto_now_add=True)

    def __str__(self):    
        return f"{self.get_type_penalties_display()} | {self.player} | {self.team_match} | {self.time}"

class Time_pause(models.Model):
    start_pause = models.TimeField()
    end_pause = models.TimeField(null=True, blank=True)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)

    def __str__(self):    
        if self.start_pause:
            return f"{self.start_pause} | {self.match}"
        elif self.start_pause and self.end_pause:
            return f"{self.start_pause} | {self.end_pause} | {self.match}"

class Occurrence(models.Model):
    name = models.CharField(max_length=50)
    details = models.CharField(max_length=200)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, null=True)
    datetime = models.TimeField(auto_now_add=True)

    def __str__(self):    
        return f"{self.name} | {self.details} | {self.details} | {self.datetime}"
    
class Banner(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to='photos_config/', null=True, blank=True)
    status = models.IntegerField(choices=Type_Banner.choices, default=Type_Banner.empty)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):    
        return f"{self.id} | {self.name} | {self.status}"

class Terms_Use(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    document = models.FileField(upload_to='document_boss/', null=True, blank=True)
    photo = models.FileField(upload_to='photo_boss/', null=True, blank=True)
    name = models.CharField(max_length=255, blank=True)
    siape = models.CharField(max_length=255, blank=True)
    email = models.EmailField(max_length=255, blank=True)
    phone = models.CharField(max_length=255, blank=True)
    accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    @property
    def date_accept_local(self):
        if self.accepted_at:
            return localtime(self.accepted_at).strftime('%d/%m/%Y %H:%M:%S')
        return "Ainda não aceitou"

    def __str__(self):
        return f"{self.usuario} - {self.date_accept_local}"
    
    class Meta:
        verbose_name = "Terms_Use"
        verbose_name_plural = "Terms_uses"

class Statement(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to='photos_config/', null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

class Statement_user(models.Model):
    statement = models.ForeignKey(Statement, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)