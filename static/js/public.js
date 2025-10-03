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
            
            const team_a = document.getElementById('team-a');
            const team_b = document.getElementById('team-b');
            const card_a = document.getElementById('card-a');
            const card_b = document.getElementById('card-b');
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
            
            break;

        case "point":
            console.log("point");
            const point = data.data;

            break;

        case "penalties":
            console.log("penalties");
            const penalties = data.data;

            break;

        case "time":
            console.log("time");
            const time = data.data;

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