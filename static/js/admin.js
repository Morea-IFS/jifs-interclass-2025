const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
const eventId = document.getElementById('scoreboard_event_id').dataset.eventId;
const socket = new WebSocket(protocol + window.location.host + "/ws/admin/" + eventId + "/");
console.log(protocol + window.location.host + "/ws/admin/" + eventId + "/");

socket.addEventListener('open', (event) => {
    console.log('WebSocket connection opened:', event);
    socket.send('Hello from client!');
});

const timer = document.getElementById('timer');

// Variáveis globais para controle do ciclo
let futsalCycleInterval;
let currentFutsalTeam = 'a'; // 'a' para casa, 'b' para visitante
let futsalPlayersA = [];
let futsalPlayersB = [];

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);

    console.log("Mensagem recebida:", data);

    switch (data.type) {
        case "match":
            console.log("match");
            const match = data.data;

            const sexo_match = document.getElementById('sexo');
            const sport_match = document.getElementById('sport');
            if(match.match_sexo === "Nenhum" && match.match_sport === "Nenhum"){
                const timer = document.getElementById('timer');
                if (timer) timer.textContent = "00:00";
            }
            const namescore = document.getElementById('name-scoreboard');

            const sets_a_match = document.getElementById('sets-a');
            const sets_b_match = document.getElementById('sets-b');
            const ball_sport = document.getElementById('ball-sport');

            const team_name_a_match = document.getElementById('team-name-a');
            const team_photo_a_match = document.getElementById('team-photo-a');
            const card_a_match = document.getElementById('card-a');
            const lack_a_match = document.getElementById('lack-a');
            const aces_a_match = document.getElementById('aces-a');
            const point_a_match = document.getElementById('point-a');
            const photoA_match = document.getElementById('team-photo-a');
            
            const team_name_b_match = document.getElementById('team-name-b');
            const team_photo_b_match = document.getElementById('team-photo-b');
            const card_b_match = document.getElementById('card-b');
            const lack_b_match = document.getElementById('lack-b');
            const aces_b_match = document.getElementById('aces-b');
            const point_b_match = document.getElementById('point-b');
            const photoB_match = document.getElementById('team-photo-b');

            if (team_name_a_match) team_name_a_match.textContent = match.team_name_a;
            if (team_photo_a_match) team_photo_a_match.textContent = match.team_photo_a;
            if (card_a_match) card_a_match.textContent = match.card_a;
            if (lack_a_match) lack_a_match.textContent = match.lack_a;
            if (point_a_match) point_a_match.textContent = match.point_a;
            if (photoA_match) photoA_match.src = match.photoA;

            if (team_name_b_match) team_name_b_match.textContent = match.team_name_b;
            if (team_photo_b_match) team_photo_b_match.textContent = match.team_photo_b;
            if (card_b_match) card_b_match.textContent = match.card_b;
            if (lack_b_match) lack_b_match.textContent = match.lack_b;
            if (point_b_match) point_b_match.textContent = match.point_b;
            if (photoB_match) photoB_match.src = match.photoB;

            if(match.aces_a && match.aces_b){
                if (aces_a_match) aces_a_match.textContent = match.aces_a;
                if (aces_b_match) aces_b_match.textContent = match.aces_b;
            }

            const aces = document.querySelectorAll(".aces");
            const sets = document.querySelectorAll(".sets");
            const timer = document.querySelectorAll(".timer");

            sets.forEach((i) => {
                i.style.display = 'none';
            });
            timer.forEach((j) => {
                j.style.display = 'flex';
            });

            if(match.match_sport === "Voleibol" || match.match_sport === "Voleibol sentado"){
                aces.forEach((t) => {
                    t.style.display = 'flex';
                });
                sets.forEach((i) => {
                    i.style.display = 'flex';
                });
                timer.forEach((j) => {
                    j.style.display = 'none';
                });
                if (sets_a_match) sets_a_match.textContent = match.sets_a;
                if (sets_b_match) sets_b_match.textContent = match.sets_b;

                console.log("Vôlei");
                if (namescore) namescore.textContent = "Sets";
                if(ball_sport) ball_sport.src = '/static/images/ball-of-volley.png';

            }else{
                console.log("Outro esporte");
                aces.forEach((t) => {
                    t.style.display = 'none';
                });
                sets.forEach((i) => {
                    i.style.display = 'none';
                });
                timer.forEach((j) => {
                    j.style.display = 'flex';
                });
                if (sets_a_match) sets_a_match.textContent = "0";
                if (sets_b_match) sets_b_match.textContent = "0";
                if (namescore) namescore.textContent = "Placar";
                if(ball_sport) ball_sport.src = '/static/images/ball-of-futsal.png';
            }
            if(match.match_sport === "Handebol"){
                if(ball_sport) ball_sport.src = '/static/images/ball-of-handball.png';
            }

            const scorematch = document.querySelectorAll('.score-ban');
            const cvolleyball = document.getElementById('container-volleyball')
            const cfutsal = document.getElementById('container-futsal')
            const moments = document.getElementById('moments')
            
            if(match.detailed == "Escalação" && match.match_sport === "Voleibol"){
                scorematch.forEach((k) => {
                    k.style.display = 'none';
                });
                if(cvolleyball) cvolleyball.style.display = "flex";
                if(cfutsal) cfutsal.style.display = "none";
                if(moments) moments.style.display = "none";
                
                // Preencher escalação do vôlei
                preencherEscalacaoVolei(match.players_a, match.players_b);

            }else if(match.detailed == "Em instantes"){
                scorematch.forEach((k) => {
                    k.style.display = 'none';
                });
                if(cvolleyball) cvolleyball.style.display = "none";
                if(cfutsal) cfutsal.style.display = "none";
                if(moments) moments.style.display = "flex";

                const team_name_a_mat = document.getElementById('moments-team-name-a');
                const team_photo_a_mat = document.getElementById('moments-team-photo-a');
                const team_name_b_mat = document.getElementById('moments-team-name-b');
                const team_photo_b_mat = document.getElementById('moments-team-photo-b');
                if (team_name_a_mat) team_name_a_mat.textContent = match.team_name_a;
                if (team_photo_a_mat) team_photo_a_mat.src = match.photoA;
                if (team_name_b_mat) team_name_b_mat.textContent = match.team_name_b;
                if (team_photo_b_mat) team_photo_b_mat.src = match.photoB;
                
                // Preencher escalação do vôlei
                preencherEscalacaoVolei(match.players_a, match.players_b);

            }else if(match.detailed == "Escalação" && match.match_sport === "Futsal"){
                scorematch.forEach((k) => {
                    k.style.display = 'none';
                });
                if(cvolleyball) cvolleyball.style.display = "none";
                if(cfutsal) cfutsal.style.display = "flex";
                if(moments) moments.style.display = "none";

                // Parar qualquer ciclo anterior
                if (futsalCycleInterval) {
                    clearInterval(futsalCycleInterval);
                }

                // Salvar os jogadores
                futsalPlayersA = match.players_a;
                futsalPlayersB = match.players_b;

                teamA = match.team_name_a
                teamB = match.team_name_b

                // Começar mostrando o time A (casa)
                currentFutsalTeam = 'a';
                mostrarTimeFutsal(currentFutsalTeam, futsalPlayersA, futsalPlayersB);
                futsalCycleInterval = setInterval(() => {
                    alternarTimeFutsal(futsalPlayersA, futsalPlayersB);
                }, 7000); 

            }else{
                scorematch.forEach((k) => {
                    k.style.display = 'flex';
                });
                if(cvolleyball) cvolleyball.style.display = "none";
                if(cfutsal) cfutsal.style.display = "none";
                if(moments) moments.style.display = "none";
                
                // Parar o ciclo do futsal se estiver ativo
                if (futsalCycleInterval) {
                    clearInterval(futsalCycleInterval);
                    futsalCycleInterval = null;
                }
            }

            stopwatch(match.seconds, match.status)
            break;

        case "point":
            console.log("point");
            const point = data.data;

            const point_a_point = document.getElementById('point-a');
            const point_b_point = document.getElementById('point-b');

            const aces_a_point = document.getElementById('aces-a');
            const aces_b_point = document.getElementById('aces-b');

            const card_goal = document.getElementById('card-goal');
            const player_name = document.getElementById('card-player-name');
            const player = document.getElementById('card-player-img')
            const team_name = document.getElementById('card-team-name');
            const team = document.getElementById('card-team-img')

            if (point_a_point) point_a_point.textContent = point.point_a;
            if (point_b_point) point_b_point.textContent = point.point_b;

            if(point.aces_a && point.aces_b){
                if (aces_a_point) aces_a_point.textContent = point.aces_a;
                if (aces_b_point) aces_b_point.textContent = point.aces_b;
            }

            if (point.player_name && point.team_name){
                if(card_goal) card_goal.style.display = "flex";

                setTimeout(() => {
                if (card_goal) card_goal.style.display = "none";
                }, 8000);

                if (player_name) player_name.textContent = point.player_name;
                if (player) player.style.backgroundImage = `url(${point.player_img})`;
                if (team_name) team_name.textContent = point.team_name;
                if (team) team.src = point.team_img;
            }

            break;

        case "penalties":
            console.log("penalties");
            const penalties = data.data;

            
            const card_a_penalties = document.getElementById('card-a');
            const lack_a_penalties = document.getElementById('lack-a');
            
            const card_b_penalties = document.getElementById('card-b');
            const lack_b_penalties = document.getElementById('lack-b');
            
            const alert_penalties = document.getElementById('alert-penalties');
            const alert_img = document.getElementById('alert-penalties-img');
            const infor_over = document.getElementById('info-overlay');

            if (card_a_penalties) card_a_penalties.textContent = penalties.card_a;
            if (lack_a_penalties) lack_a_penalties.textContent = penalties.lack_a;

            if (card_b_penalties) card_b_penalties.textContent = penalties.card_b;
            if (lack_b_penalties) lack_b_penalties.textContent = penalties.lack_b;

            if (alert_penalties) alert_penalties.textContent = penalties.penalties_player;
            if (alert_img) alert_img.src = penalties.penalties_url;
            if (infor_over) infor_over.style.display = "flex";

            setTimeout(() => {
            if (infor_over) infor_over.style.display = "none";
            }, 8000);

            break;

        case "time":
            console.log("time");
            const time = data.data;

            stopwatch(time.seconds, time.status)

            break;

        case "banner":
            console.log("banner");
            const image = data.data;

            const banner = document.querySelectorAll(".banner-scoreboard");
            const score = document.querySelectorAll('.score-ban');

            if (image.status === 1){
                banner.forEach((i) => {
                    i.style.display = 'flex';
                    i.src = image.banner;
                });
                score.forEach((j) => {
                    j.style.display = 'none';
                });
            }else{
                banner.forEach((i) => {
                    i.style.display = 'none';
                    i.src = "";
                });
                score.forEach((j) => {
                    j.style.display = 'flex';
                });
            }

            break;
        default:
            console.warn("Tipo de mensagem não reconhecido:", data.type);
    }
}

socket.onclose = function(e) {
    console.error('WebSocket fechado com código: ' + e.code);
    
    // Limpar intervalos ao fechar conexão
    if (futsalCycleInterval) {
        clearInterval(futsalCycleInterval);
    }
};

let timeoutId;

function stopwatch(time, stats) {
    console.log(time, stats)
    if (stats == 1) {
        console.log("contando")
        clearTimeout(timeoutId);
        console.log(time, stats)
        var seconds = time;
        seconds++;
        timer.textContent = formatTime(seconds);
        timeoutId = setTimeout(() => stopwatch(seconds, 1), 1000);
    } else if (stats == 2) {
        console.log("Está no status de pausa");
        clearTimeout(timeoutId);
        timer.textContent = formatTime(time);
    } else if (stats == 3) {
        console.log("Está no status de finalizado");
        clearTimeout(timeoutId);
        timer.textContent = formatTime(time);
    }
}

function formatTime(seconds) {
    if (isNaN(seconds)) {
        console.error('Valor inválido para segundos:', seconds);
        return '00:00';
    }

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${hours > 0 ? hours.toString() + ":" : ""}${minutes
        .toString()
        .padStart(2, "0")}:${remainingSeconds.toString().padStart(2, "0")}`;
}

// Funções para preencher escalações
function preencherEscalacaoVolei(playersA, playersB) {
    // Time A (Casa)
    console.log(playersA);
    console.log(playersB);
    if (playersA && playersA.length >= 6) {
        for (let i = 0; i < 3; i++) {
            const defesaElem = document.getElementById(`casa-defesa-${i+1}`);
            const ataqueElem = document.getElementById(`casa-ataque-${i+1}`);
            
            if (defesaElem && playersA[i]) {
                const img = defesaElem.querySelector('img');
                const nome = defesaElem.querySelector('.jogador-nome');
                img.src = playersA[i].photo_url || '';
                img.alt = playersA[i].name || '';
                nome.textContent = playersA[i].name || '';
                console.log(playersA[i]);
                console.log(playersA[i].photo_url);
            }
            
            if (ataqueElem && playersA[i+3]) {
                const img = ataqueElem.querySelector('img');
                const nome = ataqueElem.querySelector('.jogador-nome');
                img.src = playersA[i+3].photo_url || '';
                img.alt = playersA[i+3].name || '';
                nome.textContent = playersA[i+3].name || '';
            }
        }
    }

    // Time B (Fora)
    if (playersB && playersB.length >= 6) {
        for (let i = 0; i < 3; i++) {
            const ataqueElem = document.getElementById(`fora-ataque-${i+1}`);
            const defesaElem = document.getElementById(`fora-defesa-${i+1}`);
            
            if (ataqueElem && playersB[i]) {
                const img = ataqueElem.querySelector('img');
                const nome = ataqueElem.querySelector('.jogador-nome');
                console.log(playersB[i].photo_url)
                img.src = playersB[i].photo_url || '';
                img.alt = playersB[i].name || '';
                nome.textContent = playersB[i].name || '';
            }
            
            if (defesaElem && playersB[i+3]) {
                const img = defesaElem.querySelector('img');
                const nome = defesaElem.querySelector('.jogador-nome');
                img.src = playersB[i+3].photo_url || '';
                img.alt = playersB[i+3].name || '';
                nome.textContent = playersB[i+3].name || '';
            }
        }
    }
}

// Funções para o ciclo do futsal
function mostrarTimeFutsal(team, futsalPlayersA, futsalPlayersB) {
    console.log(`Mostrando time: ${team}`);
    console.log("eita: 1",futsalPlayersA);
    console.log("eita: 2",futsalPlayersB);
    
    // Primeiro, esconder todos os jogadores
    const todosJogadores = document.querySelectorAll('.quadra-futsal .jogador');
    todosJogadores.forEach(jogador => {
        jogador.style.display = 'none';
    });

    // Mostrar apenas os jogadores do time especificado
    if (team === 'a') {
        const jogadoresTimeA = document.querySelectorAll('.quadra-futsal .time-a');
        jogadoresTimeA.forEach(jogador => {
            jogador.style.display = 'block';
        });
        
        // Preencher dados do time A
        console.log("team a player sformando", futsalPlayersA);
        preencherTimeFutsal('a', futsalPlayersA);
    } else {
        const jogadoresTimeB = document.querySelectorAll('.quadra-futsal .time-b');
        jogadoresTimeB.forEach(jogador => {
            jogador.style.display = 'block';
        });
        
        // Preencher dados do time B
        console.log("team b player sformando", futsalPlayersB);
        preencherTimeFutsal('b', futsalPlayersB);
    }
}

function preencherTimeFutsal(team, players) {
    const funcaoToId = {
        "Goleiro": "goleiro",
        "Fixo": "fixo",
        "Ala 1": "ala1",
        "Ala 2": "ala2",
        "Pivô": "pivo"
    };
    console.log("preencherTimeFutsal",players);
    if (players) {
        players.forEach(player => {
            const idSuffix = funcaoToId[player.funcao];
            if (!idSuffix) return;
            console.log("monatndo uu pô")
            const container = document.getElementById(`${idSuffix}-${team}`);
            if (!container) return;
            console.log("monatndo players pô")

            const img = container.querySelector('img');
            const nome = container.querySelector('.nome');

            img.src = player.photo_url || '';
            img.alt = player.name || '';
            nome.textContent = player.name || '';
        });
    }
}

function alternarTimeFutsal(futsalPlayersA, futsalPlayersB) {
    // Alternar entre time A e B
    currentFutsalTeam = currentFutsalTeam === 'a' ? 'b' : 'a';
    mostrarTimeFutsal(currentFutsalTeam, futsalPlayersA, futsalPlayersB);
    console.log(`Alternando para time: ${currentFutsalTeam === 'a' ? 'Casa' : 'Visitante'}`);
}

// Limpar intervalo quando a página for fechada
window.addEventListener('beforeunload', function() {
    if (futsalCycleInterval) {
        clearInterval(futsalCycleInterval);
    }
});