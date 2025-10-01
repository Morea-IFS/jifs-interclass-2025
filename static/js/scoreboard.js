const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
const socket = new WebSocket(protocol + window.location.host + "/ws/scoreboard/");
console.log(protocol + window.location.host + "/ws/scoreboard/");

socket.addEventListener('open', (event) => {
    console.log('WebSocket connection opened:', event);
    socket.send('Hello from client!'); // Send data after connection is open
});

const timer = document.getElementById('timer');

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


                console.log("VOlei");
                if (namescore) namescore.textContent = "Sets";
                if(ball_sport) ball_sport.src = '/static/images/ball-of-volley.png';

            }else{
                console.log("utro spor");
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

            stopwatch(match.seconds, match.status)
            break;

        case "point":
            console.log("point");
            const point = data.data;

            const point_a_point = document.getElementById('point-a');
            const point_b_point = document.getElementById('point-b');

            const aces_a_point = document.getElementById('aces-a');
            const aces_b_point = document.getElementById('aces-b');

            if (point_a_point) point_a_point.textContent = point.point_a;
            if (point_b_point) point_b_point.textContent = point.point_b;

            if(point.aces_a && point.aces_b){
                if (aces_a_point) aces_a_point.textContent = point.aces_a;
                if (aces_b_point) aces_b_point.textContent = point.aces_b;
            }
            break;

        case "penalties":
            console.log("penalties");
            const penalties = data.data;

            const card_a_penalties = document.getElementById('card-a');
            const lack_a_penalties = document.getElementById('lack-a');

            const card_b_penalties = document.getElementById('card-b');
            const lack_b_penalties = document.getElementById('lack-b');

            if (card_a_penalties) card_a_penalties.textContent = penalties.card_a;
            if (lack_a_penalties) lack_a_penalties.textContent = penalties.lack_a;

            if (card_b_penalties) card_b_penalties.textContent = penalties.card_b;
            if (lack_b_penalties) lack_b_penalties.textContent = penalties.lack_b;
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