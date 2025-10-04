const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
const socket = new WebSocket(protocol + window.location.host + "/ws/public/");
console.log(protocol + window.location.host + "/ws/public/");

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

            const namescore = document.getElementById('name-scoreboard');
            
            const team_a = document.getElementById('team-a');
            const team_b = document.getElementById('team-b');
            const card_a = document.getElementById('card-a');
            const card_b = document.getElementById('card-b');
            const aces_a = document.getElementById('aces-a');
            const aces_b = document.getElementById('aces-b');
            const sets_a = document.getElementById('sets-a');
            const sets_b = document.getElementById('sets-b');
            const lack_a = document.getElementById('lack-a');
            const lack_b = document.getElementById('lack-b');
            const photo_a = document.querySelectorAll(".photo-team-a");
            const photo_b = document.querySelectorAll(".photo-team-b");
            const point_a = document.getElementById('points-a');
            const point_b = document.getElementById('points-b');

            const ball_sport = document.getElementById('ball-sport');

            if(team_a) team_a.textContent = match.team_name_a;
            if(team_b) team_b.textContent = match.team_name_b;
            if(point_a) point_a.textContent = match.point_a;
            if(point_b) point_b.textContent = match.point_b;
            if(card_a) card_a.textContent = match.card_a;
            if(card_b) card_b.textContent = match.card_b;
            if(lack_a) lack_a.textContent = match.lack_a;
            if(lack_b) lack_b.textContent = match.lack_b;
            if(ball_sport && data.ball_sport) ball_sport.src = match.ball_sport;
            photo_a.forEach((i) => {
                i.src = match.photoA;
            });
            photo_b.forEach((i) => {
                i.src = match.photoB;
            });
            updatePlayerList("teamAList", match.players_a); 
            updatePlayerList("teamBList", match.players_b); 

            const aces = document.querySelectorAll(".aces");
            const sets = document.querySelectorAll(".sets");
            const timer = document.querySelectorAll(".timer");

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
                if (sets_a) sets_a.textContent = match.sets_a;
                if (sets_b) sets_b.textContent = match.sets_b;
                if (aces_a) aces_a.textContent = match.aces_a;
                if (aces_b) aces_b.textContent = match.aces_b;

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
                if (sets_a) sets_a.textContent = "0";
                if (sets_b) sets_b.textContent = "0";
                if (aces_a) aces_a.textContent = "0";
                if (aces_b) aces_b.textContent = "0";
                if (namescore) namescore.textContent = "Tempo";
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

            const point_a_point = document.getElementById('points-a');
            const point_b_point = document.getElementById('points-b');
            const aces_a_point = document.getElementById('aces-a');
            const aces_b_point = document.getElementById('aces-b');

            if(point_a_point) point_a_point.textContent = point.point_a;
            if(point_b_point) point_b_point.textContent = point.point_b;

            if(point.aces_a >= 0  && point.aces_b >= 0){
                if (aces_a_point) aces_a_point.textContent = point.aces_a;
                if (aces_b_point) aces_b_point.textContent = point.aces_b;
            }

            break;

        case "penalties":
            console.log("penalties");
            const penalties = data.data;

            const card_a_penalties = document.getElementById('card-a');
            const card_b_penalties = document.getElementById('card-b');

            const lack_a_penalties = document.getElementById('lack-a');
            const lack_b_penalties = document.getElementById('lack-b');

            if (card_a_penalties) card_a_penalties.textContent = penalties.card_a;
            if (card_b_penalties) card_b_penalties.textContent = penalties.card_b;
            
            if (lack_a_penalties) lack_a_penalties.textContent = penalties.lack_a;
            if (lack_b_penalties) lack_b_penalties.textContent = penalties.lack_b;

            break;

        case "time":
            console.log("time");
            const time = data.data;

            stopwatch(time.seconds, time.status)

            break;

        default:
            console.warn("Tipo de mensagem não reconhecido:", data.type);
    }
}

function updatePlayerList(containerId, players) {

    const container = document.getElementById(containerId);
    if (!container) {
        console.warn("[updatePlayerList] container não encontrado:", containerId);
        return;
    }

    const borderColor = containerId === "teamAList" ? "#0000ff" : "#ff0000";

    container.innerHTML = "";

    if (!players || !Array.isArray(players) || players.length === 0) {
        return;
    }

    players.forEach(player => {

        const li = document.createElement("li");
        li.style.border = `2px solid ${borderColor}`;
        li.dataset.name = player.name;

        const number = player.number !== undefined ? player.number : "?"; 

        li.innerHTML = `
            <div class="player-photo">
                <img src="${player.photo_url || '/static/images/person.png'}" 
                     alt="foto de ${player.name}" 
                     class="photo"/>
            </div>
            <div class="player-text-informations">
                <p class="player-name"><span>${player.name}</span></p>
                <div class="player-instagram">
                    <img src="/static/images/logo-morea-sports.svg" 
                         alt="" 
                         aria-hidden="true" 
                         class="instagram"/>
                    <a>(N° ${number})</a>
                </div>
            </div>
        `;

        container.appendChild(li);
    });

}

socket.onclose = function(e) {
    console.error('WebSocket fechado com código: ' + e.code);
};

let timeoutId;

function stopwatch(time, stats) {
    if (stats == 1) {
        clearTimeout(timeoutId);
        var seconds = time;
        seconds++;
        timer.textContent = formatTime(seconds);
        timeoutId = setTimeout(() => stopwatch(seconds, 1), 1000);
    } else if (stats == 2) {
        clearTimeout(timeoutId);
        timer.textContent = formatTime(time);
    } else if (stats == 3) {
        clearTimeout(timeoutId);
        timer.textContent = formatTime(time);
    }
}

function formatTime(seconds) {
    if (isNaN(seconds)) {
        return '00:00';
    }

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${hours > 0 ? hours.toString() + ":" : ""}${minutes
        .toString()
        .padStart(2, "0")}:${remainingSeconds.toString().padStart(2, "0")}`;
}