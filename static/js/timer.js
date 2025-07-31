const socket = new WebSocket('ws://' + window.location.host + '/ws/placar/'),
 timer = document.getElementById('timer'),
 titleset = document.getElementById("title-set");

socket.onmessage = function(e) {
    const data = JSON.parse(e.data),
     pointsA = document.getElementById('points-a'),
     pointsB = document.getElementById('points-b'),
     pointsAscore = document.getElementById('points-a-score'),
     pointsBscore = document.getElementById('points-b-score'),
     acesA = document.getElementById('aces_aa'),
     acesB = document.getElementById('aces_bb'),
     acesAscore = document.getElementById('aces_aa_score'),
     acesBscore = document.getElementById('aces_bb_score'),
     teamA = document.getElementById('team-a'),
     teamB = document.getElementById('team-b'),
     lackA = document.getElementById('lack-a'),
     lackB = document.getElementById('lack-b'),
     cardA = document.getElementById('card-a'),
     cardB = document.getElementById('card-b'),
     acesA1 = document.getElementById('aces-a'),
     acesB1 = document.getElementById('aces-b'),
     namescoreboard = document.getElementById('name-scoreboard'),
     teamAscore = document.getElementById('team-a-score'),
     teamBscore = document.getElementById('team-b-score'),
     setsA = document.getElementById('timer'),
     setsB = document.getElementById('sets-team-b'),
     setscard = document.getElementById('sets-or-card'),
     teamAcolor = document.getElementById('team_a_color'),
     teamBcolor = document.getElementById('team_b_color'),
     teamA2color = document.getElementById('team_a2_color'),
     teamB2color = document.getElementById('team_b2_color'),
     teamA3color = document.getElementById('team_a3_color'),
     teamB3color = document.getElementById('team_b3_color'),
     photoA = document.getElementById('photo-team-a'),
     photoB = document.getElementById('photo-team-b'),
     photoAB = document.getElementById('photo-team-a-b'),
     photoBB = document.getElementById('photo-team-b-b'),
     imgsexo = document.getElementById('img-sexo'),
     sexocolor = document.getElementById('sexo-color'),
     ballsport = document.getElementById('ball-sport'),
     sets_on = document.getElementById('sets_on'),
     scoreboard1 = document.getElementById('scoreboard-1'),
     scoreboard2 = document.getElementById('scoreboard-2'),
     acesimgA = document.getElementById('aces-img-a'),
     acesimgB = document.getElementById('aces-img-b'),
     bannerScoreboard = document.getElementById('banner-scoreboard'),
     FooterBoard = document.getElementById('footer-project'),
     SectionBoard = document.getElementById('section-project');
    console.log(data)
    if (pointsA) pointsA.textContent = data.points_a;
    if (pointsB) pointsB.textContent = data.points_b;
    if (namescoreboard) namescoreboard.textContent = data.name_scoreboard;
    if (setscard) setscard.textContext = data.aces_or_card;
    if (pointsAscore) pointsAscore.textContent = data.points_a_score;
    if (pointsBscore) pointsBscore.textContent = data.points_b_score;  
    if (setsA) setsA.textContent = data.sets_a;
    if (setsB) setsB.textContent = data.sets_b; 
    if (lackA) lackA.textContent = data.lack_a;
    if (lackB) lackB.textContent = data.lack_b; 
    if (cardA) cardA.textContent = data.card_a;
    if (cardB) cardB.textContent = data.card_b;
    if (acesA1) acesA1.textContent = data.aces_a_score;
    if (acesB1) acesB1.textContent = data.aces_b_score; 
    if (acesA) acesA.textContent = data.aces_a;
    if (acesB) acesB.textContent = data.aces_b;
    if (acesAscore) acesAscore.textContent = data.aces_a_score;
    if (acesBscore) acesBscore.textContent = data.aces_b_score;
    if (teamA2color) teamA2color.textContent = data.lack_a;
    if (teamB2color) teamB2color.textContent = data.lack_b;
    if (teamA3color) teamA3color.textContent = data.aces_or_card_a;
    if (teamB3color) teamB3color.textContent = data.aces_or_card_b;
    if (teamA) teamA.textContent = data.team_a;
    if (teamB) teamB.textContent = data.team_b;
    if (teamAscore) teamAscore.textContent = data.team_a_score;
    if (teamBscore) teamBscore.textContent = data.team_b_score;
    if (photoA) photoA.src = data.photoA;
    if (photoB) photoB.src = data.photoB;
    if (photoAB) photoAB.src = data.photoA;
    if (photoBB) photoBB.src = data.photoB;
    if (teamAcolor) team_a_color.style.backgroundColor = data.teamAcolor;
    if (teamBcolor) team_b_color.style.backgroundColor = data.teamBcolor;
    if (teamA2color) team_a2_color.style.backgroundColor = data.teamAcolor;
    if (teamB2color) team_b2_color.style.backgroundColor = data.teamBcolor;
    if (teamA3color) team_a3_color.style.backgroundColor = data.teamAcolor;
    if (teamB3color) team_b3_color.style.backgroundColor = data.teamBcolor;
    if (imgsexo) imgsexo.src = data.img_sexo;
    if (sexocolor) sexocolor.style.color = data.sexo_color;
    if (sexocolor) sexocolor.textContent = data.sexo_text;
    if (ballsport) ballsport.src = data.ball_sport;
    if (bannerScoreboard) bannerScoreboard.src = data.banner_score;

    if(SectionBoard) SectionBoard.style.display = data.banner_status_score ? 'none' : 'flex';
    if(FooterBoard) FooterBoard.style.display = data.banner_status_score ? 'none' : 'flex';
    if(bannerScoreboard) bannerScoreboard.style.display = data.banner_status_score ? 'block' : 'none';
    
    
    if (data.sets_time_auto) {
        if(setsB) setsB.style.display = 'none';
        if(scoreboard1) scoreboard1.style.display = 'none';
        if(scoreboard2) scoreboard2.style.display = 'none';
        if(acesimgA) acesimgA.style.display = 'none';
        if(acesimgB) acesimgB.style.display = 'none';
        if(acesA1) acesA1.style.display = 'none';
        if(acesB1) acesB1.style.display = 'none'; 
        stopwatch(data.seconds, data.status)
    }else if (data.sets_time_auto === false) {
        if(setsB) setsB.style.display = 'flex';
        if(scoreboard1) scoreboard1.style.display = 'flex';
        if(scoreboard2) scoreboard2.style.display = 'flex';
        if(acesimgA) acesimgA.style.display = 'flex';
        if(acesimgB) acesimgB.style.display = 'flex';
        if(acesA1) acesA1.style.display = 'flex';
        if(acesB1) acesB1.style.display = 'flex'; 
        }
};

socket.onclose = function(e) {
    console.error('WebSocket fechado com código: ' + e.code);
};

let timeoutId;

function stopwatch(time, stats) {
    if (stats == 1) {
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