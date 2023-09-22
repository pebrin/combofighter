var test_var = undefined;
var room_name = undefined; 
var round_time = undefined;
var results_time = undefined;
var game_results_time = undefined;
var num_rounds = undefined;
var cur_round = undefined;
var next_event_time = undefined;
var countdown = undefined;
var server_states = undefined;
var my_id = undefined;
var my_name = undefined;
var my_word = undefined;
var prompts = [];
var admins = [];

var audio_context = null;
var mute = false;
var non_bomb_audio_gain_node = null;
var bomb_audio_gain_node = null;
var audio_game_tick = [null, null];
var audio_game_play_word_zero = [null, null];
var audio_game_play_word_normal = [null, null];
var audio_game_play_word_good = [null, null];
var audio_game_play_word_excellent = [null, null];
var audio_game_play_word_wonderful = [null, null];
var audio_game_play_time_out = [null, null];
var audio_round_win = [null, null];
var audio_round_lose = [null, null];
var audio_game_win = [null, null];
var audio_game_lose = [null, null];
var audio_vars = [audio_game_tick, audio_game_play_word_zero, audio_game_play_word_normal, audio_game_play_word_good, audio_game_play_word_excellent, audio_game_play_word_wonderful, audio_game_play_time_out, audio_round_win, audio_round_lose, audio_game_win, audio_game_lose]

var bomb_tick = null;
var bomb_tick_timeout = null;
var bomb_audio_rate = 1;
var bomb_audio_duration = null;

function init_vars(template_vars){
	round_time = template_vars['ROUND_TIME'];
	round_results_time = template_vars['ROUND_RESULTS_TIME'];
	game_results_time = template_vars['GAME_RESULTS_TIME'];
	num_rounds = template_vars['NUM_ROUNDS'];
	server_states = template_vars['SERVER_STATES'];
	room_name = template_vars['ROOM_NAME'];
	audio_path = template_vars['audio_path'];
	audio_game_tick[0] = audio_path+template_vars['audio_game_tick'];
	audio_game_play_word_zero[0] = audio_path+template_vars['audio_game_play_word_zero'];
	audio_game_play_word_normal[0] = audio_path+template_vars['audio_game_play_word_normal'];
	audio_game_play_word_good[0] = audio_path+template_vars['audio_game_play_word_good'];
	audio_game_play_word_excellent[0] = audio_path+template_vars['audio_game_play_word_excellent'];
	audio_game_play_word_wonderful[0] = audio_path+template_vars['audio_game_play_word_wonderful'];
	audio_game_play_time_out[0] = audio_path+template_vars['audio_game_play_time_out'];
	audio_round_win[0] = audio_path+template_vars['audio_round_win'];
	audio_round_lose[0] = audio_path+template_vars['audio_round_lose'];
	audio_game_win[0] = audio_path+template_vars['audio_game_win'];
	audio_game_lose[0] = audio_path+template_vars['audio_game_lose'];
}

function generate_scoreboard(board_info){
	var tbody = document.querySelector('#results_table_body');
	for (i = 0; i < board_info.length; i++){
		var table_row = tbody.insertRow(0);
		table_row.id=board_info[i][0];
		var cell0 = table_row.insertCell(0);
		cell0.className="round_ready_check";
		cell0.innerHTML="<span class='results_user_right_arrow'>▶</span><span class='user_name'>"+board_info[i][1]+"</span><span class='results_user_left_arrow'>◀</span>";
		var cell1 = table_row.insertCell(1);
		cell1.className="user_round_word";
		cell1.innerHTML="";
		var cell2 = table_row.insertCell(2);
		cell2.className="user_score";
		cell2.innerHTML=board_info[i][4];
	}
}

function update_scoreboard(board_info){
	for (i = 0; i < board_info.length; i++){
		var word_display = "None!";
		if (board_info[i][2] != -1){
			word_display = board_info[i][2].toUpperCase();
		}
		var row = document.getElementById(board_info[i][0]);
		row.querySelector('.user_round_word').textContent = word_display+" (+"+board_info[i][3]+")";
		row.querySelector('.user_score').textContent=board_info[i][4];
	}
	sortTable('results_table_body', compare_score);
}

//x and y are row elements in the scoreboard
function compare_score(x, y){
	return parseInt(x.querySelectorAll("td")[2].innerHTML) < parseInt(y.querySelectorAll("td")[2].innerHTML);
}

//n^2 sort, but our tables are super small
function sortTable(id, compare_function) {
	var table, rows, switching, i, x, y, shouldSwitch;
	table = document.getElementById(id);
	switching = true;
	while (switching) {
		switching = false;
		rows = table.querySelectorAll("tr");
		for (i = 0; i < (rows.length - 1); i++) {
			shouldSwitch = false;
			x = rows[i];
			y = rows[i + 1];
			if (compare_function(x, y)) {
				shouldSwitch= true;
				break;
			}
		}
		if (shouldSwitch) {
			rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
			switching = true;
		}
	}
}


function wipe_scoreboard_words(){
	var words = document.querySelectorAll('.user_round_word');
	for (i = 0; i < words.length; i++){
		words[i].textContent = "";
	}
}

function wipe_scoreboard_scores(){
	var words = document.querySelectorAll('.user_score');
	for (i = 0; i < words.length; i++){
		words[i].textContent = "0";
	}
}

function add_user_to_scoreboard(id, name){
	var tbody = document.querySelector('#results_table_body');
	var table_row = tbody.insertRow(tbody.children.length);
	table_row.id=id;
	var cell0 = table_row.insertCell(0);
	cell0.className="round_ready_check";
	cell0.innerHTML="<span class='results_user_right_arrow'>▶</span><span class='user_name'>"+name+"</span><span class='results_user_left_arrow'>◀</span>";
	var cell1 = table_row.insertCell(1);
	cell1.className="user_round_word";
	cell1.innerHTML="";
	var cell2 = table_row.insertCell(2);
	cell2.className="user_score";
	cell2.innerHTML=0;
}

function remove_user_from_scoreboard(id){
	var user_row = document.getElementById(id);
	user_row.parentNode.removeChild(user_row);
}

function reset_ready_indicators(){
	var usernames = document.querySelectorAll('.round_ready_check');
	for (i = 0; i < usernames.length; i++){
		usernames[i].querySelector('.user_name').style.color='gray';
	}
}

function set_word_input_mode(val){
	if (val == false){
		document.getElementById('word_entry_box').contentEditable='false';
		//$(word_entry_box).css("visibility", "hidden");
		/*$('#word_entry_box').animate({
            opacity:1
        }, 300);*/
		//$('#word_entry_box').css("contentEditable", "false");
		//$(word_entry_reply).css("visibility", "visible");
		$('#word_entry_reply').animate({
            opacity:1
        }, 500);
		//document.getElementById("word_entry_box").textContent = "";
		stop_bomb_sound();
		$('#chat_textbox').focus();
	}
	else {
		document.getElementById('word_entry_box').contentEditable='true';
		$('#word_entry_box').animate({
            color:'#EEEEEE'
        }, 500);
		$('#word_score').animate({
            color:'#EEEEEE'
        }, 500);
		//$('#word_entry_box').css("contentEditable", "true");
		$('#word_entry_reply').animate({
            opacity:0
        }, 300);
		$('#word_entry_reply').promise().done(function(){$('#word_entry_reply').text("");});
		//$(word_entry_box).css("visibility", "visible");
		//$(word_entry_reply).css("visibility", "hidden");
		if (document.getElementById('chat_textbox').value.length == 0){
			$('#word_entry_box').focus();
		}
	}
}

function populate_prompts_table(prompts){
	$('#prompts_table').empty();
	if (prompts.length%2==0){
		var midpoint = Math.floor(prompts.length/2);
		for (i = 0; i < midpoint; i++){
			$('#prompts_table').append('<tr><td class="pr'+i+' letters">'+prompts[i][0].toUpperCase()+'</td><td class="pr'+i+'">'+prompts[i][1]+'</td><td class="pr'+(i+midpoint)+' letters">'+prompts[i+midpoint][0].toUpperCase()+'</td><td class="pr'+(i+midpoint)+'">'+prompts[i+midpoint][1]+'</td></tr>');
		}
	}
	else if (prompts.length%2==1){
		var midpoint = Math.floor(prompts.length/2);
		for (i = 0; i < midpoint; i++){
			$('#prompts_table').append('<tr><td class="pr'+i+' letters">'+prompts[i][0].toUpperCase()+'</td><td class="pr'+i+'">'+prompts[i][1]+'</td><td class="pr'+(i+midpoint+1)+' letters">'+prompts[i+midpoint+1][0].toUpperCase()+'</td><td class="pr'+(i+midpoint+1)+'">'+prompts[i+midpoint+1][1]+'</td></tr>');
		}
		$('#prompts_table').append('<tr><td class="pr'+(midpoint)+' letters">'+prompts[midpoint][0].toUpperCase()+'</td><td class="pr'+(midpoint)+'">'+prompts[midpoint][1]+'</td></tr>');
	}

}

function update_round_info(cur_round, num_rounds){
	document.getElementById("rnumber").textContent = cur_round;
	document.getElementById("rtotal").textContent = num_rounds;
}

function update_timer(element, event_time){
	document.getElementById(element).textContent = event_time;
	next_event_time = event_time;
	clearInterval(countdown);
	countdown = setInterval(function(){
		 next_event_time--; 
		 if (next_event_time >= 0){
		 	document.getElementById(element).textContent = next_event_time;
			} 
		}, 1000);
}

function add_chat_message(id, name, msg){
	var objDiv = document.getElementById("messages");
	var li = document.createElement("li");
	li.className ="user_message";
	var timestamp = document.createElement("span");
	var now = new Date();
	timestamp.innerHTML =  now.getHours()+":"+("0"+now.getMinutes()).slice(-2);
	timestamp.className="chat_timestamp";
	var span_name = document.createElement("span");
	span_name.innerHTML = name;
	span_name.className = "user_name";
	for (i = 0; i < admins.length; i++){
		if (admins[i] == id)
			span_name.className += " admin";
	}
	var span_message = document.createElement("span");	
	$(span_message).text(": "+msg);
	li.appendChild(timestamp);
	li.appendChild(span_name);
	li.appendChild(span_message);
	objDiv.appendChild(li);

	objDiv.scrollTop = objDiv.scrollHeight;
}

function add_system_message(msg){
	var objDiv = document.getElementById("messages");
	var li = document.createElement("li");
	var span_message = document.createElement("span");	
	span_message.innerHTML = msg;
	span_message.className="system_message";
	var timestamp = document.createElement("span");
	var now = new Date()
	//timestamp.innerHTML = now.toLocaleTimeString([], {hour: 'numeric', minute:'numeric'});
	timestamp.innerHTML = now.getHours()+":"+("0"+now.getMinutes()).slice(-2);
	timestamp.className="chat_timestamp";
	li.appendChild(timestamp);
	li.appendChild(span_message);
	objDiv.appendChild(li);
	objDiv.scrollTop = objDiv.scrollHeight;
}

function prompt_color(v){
	var shift_val = 5;
	var scale_val = 3;
	var h = (1+((v-shift_val)/scale_val)/(1+Math.abs((v-shift_val)/scale_val)))/2;
	//console.log("h:" +h)
	h = 1 - h; //blue is worse
	return "hsl(" + parseInt(240*h) + ", 100%, 80%)";
}


function load_sound(i){
	var request = new XMLHttpRequest();
	request.open('GET', audio_vars[i][0], true);
	request.responseType = 'arraybuffer';
	request.onload = function () {
		audio_context.decodeAudioData(request.response, function(buffer){ audio_vars[i][1]=buffer; }, function (e) {  });
	}
	request.send();
}

function load_sounds(){
	for (i = 0; i < audio_vars.length; i++){
		load_sound(i);
	}
}

function play_sound(sound_var){
	if (!mute){
		var source = audio_context.createBufferSource();
		source.buffer = sound_var[1];            
		source.connect(non_bomb_audio_gain_node); 
		non_bomb_audio_gain_node.connect(audio_context.destination);           
		source.start(0);       
	}                   
}

function progressive_bomb_tick(total_event_time){
	//below 20 seconds increase by 0.025 per tick event, below 10 seconds increase by 0.050 per tick event
	if (total_event_time > 20)
		bomb_audio_rate = 1;
	else if (total_event_time > 10)
		bomb_audio_rate = 1 + (20 - total_event_time)*0.025;
	else
		bomb_audio_rate = 1.25 + total_event_time*0.06;
	play_bomb_sound(bomb_audio_rate);
	progressive_bomb_tick_helper();
}

function progressive_bomb_tick_helper(){
	//play_bomb_sound(bomb_audio_rate);
	bomb_audio_duration = 1000*bomb_tick.buffer.duration/bomb_audio_rate;
	bomb_tick_timeout = setTimeout(function(){
			var rate_increase = 0;
			if (next_event_time > 20){
				rate_increase = 0.0;
			} else if (next_event_time > 10){
				rate_increase = 0.025;
			}
			else if (next_event_time > 0){
				rate_increase = 0.06;
			}
			bomb_audio_rate += rate_increase;
			bomb_tick.playbackRate.value=bomb_audio_rate
			//console.log("rate is now " + bomb_audio_rate);
			
			progressive_bomb_tick_helper();
		}, bomb_audio_duration);

}

function play_bomb_sound(rate){
	if (!mute){
		bomb_tick = audio_context.createBufferSource();
		bomb_tick.buffer = audio_game_tick[1];
		bomb_tick.playbackRate.value = rate; 
		bomb_tick.loop = true;
		bomb_tick.connect(bomb_audio_gain_node); 
		bomb_audio_gain_node.connect(audio_context.destination);     
		bomb_tick.start(0);       
	}                   
}

function stop_bomb_sound(){
	clearTimeout(bomb_tick_timeout);
	if (bomb_tick){
		bomb_audio_rate = 1;
		bomb_tick.stop();  
	}                     
}


$(function () {
//var socket = io({reconnection:false,transports:["websocket"]});
var socket = io({reconnection:false});

window.AudioContext = window.AudioContext||window.webkitAudioContext;
audio_context = new AudioContext();
load_sounds();
bomb_audio_gain_node = audio_context.createGain();
non_bomb_audio_gain_node = audio_context.createGain();
bomb_audio_gain_node.gain.value=0.5;
non_bomb_audio_gain_node.gain.value=1;

$("#chat_textbox").keypress(function (e) {
	if(e.which == 13 && !e.shiftKey) {        
		if ($('#chat_textbox').val()){
			socket.emit('chat_message', $('#chat_textbox').val());
		}
		$('#chat_textbox').val('');
		return false;
	}
});

$("#speaker_icon").click(function (e){
	mute = !mute;
	if (mute){
		$("#speaker_icon")[0].style.opacity = 0.3;
		bomb_audio_gain_node.gain.value=0;
		non_bomb_audio_gain_node.gain.value=0;
	}
	else {
		$("#speaker_icon")[0].style.opacity = 1;
		bomb_audio_gain_node.gain.value=0.5;
		non_bomb_audio_gain_node.gain.value=1;
	}
});



socket.on('connect', function(){
	add_system_message("Welcome to ComboFighter! Type '!help' for options.");
});

socket.on('disconnect', function(){
	add_system_message("Error: Lost connection to server. Try reloading the page to reconnect.");
});

socket.on('chat_message', function(msg){
	add_chat_message(msg['id'],msg['cname'],msg['m']);
});

socket.on('system_message', function(msg){
	add_system_message(msg);
});

socket.on('setup', function(msg){
	document.getElementById("comboname").textContent = msg['name'];
	admins = msg['admins'];
	my_id = msg['id'];
	my_name = msg['name'];
	generate_scoreboard(msg['scoreboard']);
	prompts = msg['prompts'];
	populate_prompts_table(msg['prompts']);
	document.getElementById(my_id).className="my_scoreboard_row";
	document.getElementById(my_id).title="This is you!";
	$('#loading_box').hide();
//	$('#game_body').fadeIn();
	$('#game_body').css({opacity: 0, display: 'flex'}).animate({
            opacity: 1
        }, 500);
});

$('#word_entry_box').on('paste', function (e) {
	e.preventDefault();
	return false;
});

$("#word_entry_box").keypress(function (e) {
	//console.log('pressed');
	if(e.which == 13) {        
		if ($('#word_entry_box').text()){
			socket.emit('gameplay_user_submit', $('#word_entry_box').text());
			my_word = $('#word_entry_box').text();
		}
		set_word_input_mode(false);
		return false;
	} 
	user_input = document.getElementById('word_entry_box').textContent;
	if (user_input.length > 30){
		e.preventDefault();
		return false;
	}
});

$("#word_entry_box").keyup(function (e) {/*
	var old_matches = document.querySelectorAll('.pr').querySelectorAll('.letters');
	for (i = 0; i < old_matches.length; i++){
		old_matches[i].style.color="";
		old_matches[i].style.textShadow="";
	}*/
	if(e.which != 13) {        
		user_input = document.getElementById('word_entry_box').textContent.toLowerCase();
		var sum = 0;
		var multiplier = 0;
		for (i = 0; i < prompts.length; i++){
			var n = user_input.indexOf(prompts[i][0]);
			if (n != -1){
				sum += prompts[i][1];
				multiplier += 1;
				//console.log("matches " + prompts[i][0]);
				var matches = document.querySelectorAll('.pr'+i);
				for (j = 0; j < matches.length; j++){
					matches[j].style.color=prompt_color(prompts[i][1]);
					matches[j].style.textShadow="-1px -1px 2px #000, 1px -1px 2px #000, -1px 1px 2px #000, 1px 1px 2px #000";
					matches[j].style.fontWeight="900";
				}
			}
			else{
				var matches = document.querySelectorAll('.pr'+i);
				for (j = 0; j < matches.length; j++){
					matches[j].style.color="";
					matches[j].style.textShadow="";
					matches[j].style.fontWeight="";
				}
			}
		}
		document.getElementById('word_score').textContent = sum*multiplier;
	} 
});



socket.on('gameplay_response', function(msg){
	document.getElementById("word_entry_reply").textContent = msg['msg'];
	$('#word_entry_reply').animate({
            opacity: 1
        }, 500);
	if (msg['score'] == 0){
			play_sound(audio_game_play_word_zero);
			$('#word_entry_box').animate({
		        color:'red'
		    }, 300);
			$('#word_score').animate({
		        color:'red'
		    }, 300);
		}
	else{
			play_sound(audio_game_play_word_normal); 
			$('#word_entry_box').animate({
		        color:'#1DEE2F'
		    }, 300);
			$('#word_score').animate({
		        color:'#1DEE2F'
		    }, 300);
		}
	if (msg['score'] >= 200){
		setTimeout( function() { play_sound(audio_game_play_word_wonderful) }, 1500);
	}
	else if (msg['score'] >= 100){
		setTimeout( function() { play_sound(audio_game_play_word_excellent) }, 1500);
	}
});

socket.on('round_start', function(msg){
	if ($('#game_winner_box').is(':visible')){
		$('#game_winner_box').hide();
		$('#game_body').fadeIn();
	}
	if ($('#idle_box').is(':visible')){
		$('#idle_box').hide();
		$('#game_body').fadeIn();
	}
	$('#word_entry_box').text("");
	$('#word_score').text("0");
	my_word = undefined;
	reset_ready_indicators();
	wipe_scoreboard_words();
	prompts = msg['prompts'];
	populate_prompts_table(msg['prompts']);
	set_word_input_mode(true);
	$('#word_entry_box').val('');
	$('#winner_box').fadeOut();
	$('#best_word').animate({
            opacity: 0
        }, 500);
	//document.getElementById("best_word").textContent = '';
	document.getElementById("time_descriptor").textContent = "Time remaining: ";
	update_round_info(msg['cround'], msg['trounds']);
	if (document.getElementById('chat_textbox').value.length == 0){
		$('#word_entry_box').focus();
	}
	update_timer("rseconds", msg['time']);
	progressive_bomb_tick(msg['time']);
});

socket.on('round_end', function(msg){
	stop_bomb_sound();

	if (my_word == null){
		play_sound(audio_game_play_time_out);
	}
	set_word_input_mode(false);
	update_scoreboard(msg['scoreboard']);
	document.getElementById("best_word").textContent = msg['bestword'];
	$('#best_word').animate({
            opacity: 1
        }, 500);
	document.getElementById("time_descriptor").textContent = "Next round in: ";
	winner = msg['winner'];
	var win = false;
	for (i = 0; i < winner.length; i++){
		if (winner[i] == my_name)
			win = true;
	}
	if (win)
		play_sound(audio_round_win);
	else
		play_sound(audio_round_lose);
	if (winner.length==1){
			document.getElementById("round_win_desc").textContent = "This round's winner is: ";
			document.getElementById("winner").textContent = winner[0];
	} else if (winner.length==0){
			document.getElementById("round_win_desc").textContent = "No one scored any points this round!";
			document.getElementById("winner").textContent = "";
	} else {
			document.getElementById("round_win_desc").textContent = "This round's winners are: ";
			document.getElementById("winner").textContent = winner.join(", ");
	}
	$('#winner_box').fadeIn();
	update_timer("rseconds", msg['time']);
});

socket.on('game_end', function(msg){
	winner = msg['winner'];
	var win = false;
	for (i = 0; i < winner.length; i++){
		if (winner[i] == my_name)
			win = true;
	}
	if (win)
		play_sound(audio_game_win);
	else
		play_sound(audio_game_lose);
	if (winner.length==1){
			document.getElementById("game_winner_info").innerHTML = "The winner is: <span class='user_name'>"+winner[0]+"</span>!!!";
	} else if (winner.length==0){
			document.getElementById("game_winner_info").innerHTML = "Somehow, no one scored any points this game!";
	} else {
			document.getElementById("game_winner_info").innerHTML = "Unbelievable! There was a tie!!! The winners are: <span class='user_name'>"+winner.join("</span>, <span class='user_name'>")+"</span>";

	}
	update_timer("next_game_time", msg['time']);
	$('#game_body').hide();
	$('#game_winner_box').fadeIn();
	wipe_scoreboard_scores();
});

socket.on('ready_user', function(msg){
	document.getElementById(msg).querySelector('.round_ready_check').querySelector('.user_name').style.color='black';
});

socket.on('admin_change', function(msg){
	if (msg['is_admin']){
		admins.push(msg['id']);
		add_system_message('<span class="user_name admin">' + msg['name'] + "</span> is now an admin for this room.");
	} else{
		for (i = 0; i < admins.length; i++){
			if (admins[i] == msg['id']){
				add_system_message('<span class="user_name">' + msg['name'] + "</span> is no longer an an admin for this room.");
				admins.splice(i, 1);
				break;
			}
		}
	}
});

socket.on('temp_join_game', function(msg){
	add_system_message(msg['msg']);
	document.getElementById(msg['id']).querySelector('.round_ready_check').querySelector('.user_name').style.setProperty("text-decoration", "none");
});

socket.on('temp_leave_game', function(msg){
	add_system_message(msg['msg']);
	document.getElementById(msg['id']).querySelector('.round_ready_check').querySelector('.user_name').style.setProperty("text-decoration", "line-through");
});

socket.on('idle', function(msg){
	stop_bomb_sound();
	$('#game_body').hide();
	$('#game_winner_box').hide();
	$('#idle_box').fadeIn();
	//add_system_message(msg['msg']);
	//document.getElementById(msg).querySelector('.round_ready_check').querySelector('.user_name').style.color='black';
});



socket.on('connect_message', function(msg){
	add_system_message('<span class="user_name">' + msg['name'] + "</span> has joined the fight!");
	add_user_to_scoreboard(msg['id'], msg['name']);
	test_var = msg
});

socket.on('disconnect_message', function(msg){
	add_system_message('<span class="user_name">' + msg['name'] + "</span> has left the fight!");
	remove_user_from_scoreboard(msg['id']);
});
});
