from flask import Flask, request, copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room
from threading import Timer, Thread, Condition
from enum import Enum
from operator import itemgetter

import flask_socketio

import time
import os
import sys
import copy
import random
import dicotools
import chattools
import flask_socketio

class ComboFighter:
	
	#The following two list events handled by each side -- events the server handles on its side, and events the client handles on its side.
	server_events = Enum('server_events', 'connect disconnect chat_message gameplay_user_submit join_game leave_game')
	#client_events = Enum('client_events', 'setup chat_message system_message gameplay_response round_start round_end game_end ready_user connect_message disconnect_message')

	state = Enum('State', 'idle game_start in_round round_end game_end')
		
	def __init__(self, app, index_entry, room_name, game_name, socketio):
		self.app = app
		self.index = index_entry[0]
		self.index_lock = index_entry[1]
		self.room_name = room_name
		self.game_name = game_name
		self.socketio = socketio
		self.type="ComboFighter"

		#in seconds:
		self.defaults = {'ROUND_TIME':40,
						'ROUND_RESULTS_TIME':12, 
						'GAME_RESULTS_TIME':20,
						'NUM_ROUNDS':10,
						'NUM_PROMPTS':12,
						'PROMPT_DIFFICULTY':3.5, #value between 0 and 10
						'room_name':room_name,
						'game_name':game_name, 
						'audio_path':'/sounds/',
						'audio_game_tick':'bptick.wav',
						'audio_game_play_word_zero':'350923__cabled-mess__hurt-c-01.wav',
						'audio_game_play_word_normal':'371190__plutoniumisotop__lock.wav',
						'audio_game_play_word_good':'371190__plutoniumisotop__lock.wav',
						'audio_game_play_word_excellent':'super_hexagon_excellent.wav',
						'audio_game_play_word_wonderful':'super_hexagon_wonderful.wav',
						'audio_game_play_time_out':'350923__cabled-mess__hurt-c-01.wav',
						'audio_round_win':'350876__cabled-mess__coin-c-09.wav',
						'audio_round_lose':'placeholder.wav',
						'audio_game_win':'171671__fins__success-1.wav',
						'audio_game_lose':'269184__mickleness__chat-message-5-trade-mine.mp3'
						}
        
		self.round_time = self.defaults['ROUND_TIME']
		self.round_results_time = self.defaults['ROUND_RESULTS_TIME']
		self.game_results_time = self.defaults['GAME_RESULTS_TIME']
		self.num_rounds = self.defaults['NUM_ROUNDS']
		self.num_prompts = self.defaults['NUM_PROMPTS']
		self.prompt_difficulty = self.defaults['PROMPT_DIFFICULTY']

		self.users = [] 
		self.prompts_list = []
		self.results_list = [] #(uid, name, word, round_score, game_score)
		self.last_round_results_list = [] #same as above
		self.server_state = ComboFighter.state.idle
		self.all_players_submitted = False
		self.all_players_submitted_cv = Condition()
		self.next_event_time = None
		self.round_number = None
		self.best_word_message = None
		self.winners = []

		self.next_state = self.start_game
		self.game_active = True
		self.room_active = True

	def get_user(self, uid=False, name=False):
		if (uid):
			for user in self.users:
				if user.uid == uid:
					return user
		elif (name):
			for user in self.users:
				if user.name == name:
					return user

	def player_registered(self, uid):
		for user in self.users:
			if user.uid == uid:
				return True
		return False

	def num_admins(self):
		n = 0
		for user in self.users:
			if user.is_admin:
				n+=1
		return n

	def admin_ids(self):
		r = []
		for user in self.users:
			if user.is_admin:
				r.append(user.uid)
		return r

	def html_player_list(self):
		player_list = []
		for user in self.users:
			classes = "user_name"
			if user.is_admin:
				classes += " admin"
			if not user.in_game:
				classes += " afk"
			player_list.append("<span class='"+classes+"'>"+user.name+"</span>")
		return "Player list: "+ ", ".join(player_list)

	def register_user(self):
		join_room(self.room_name)
		uid = request.sid
		u = User(uid)
		cname = u.name
		if len(self.users) == 0:
			u.is_admin=True
		self.users.append(u)
		self.results_list.append([uid, cname, -1, 0, 0])
		emit('connect_message', {'name':cname, 'id':uid}, broadcast=True, room=self.room_name)
		if (u.is_admin):
			emit('admin_change', {'name':cname, 'id':uid, 'is_admin':u.is_admin}, broadcast=True, room=self.room_name)
		emit('setup', {'name':cname, 'id':uid, 'prompts':self.prompts_list, 'scoreboard':self.last_round_results_list, 'admins':self.admin_ids()})
		self.last_round_results_list.append([uid, cname, -1, 0, 0])
		if not self.game_active:
			self.game_active = True

		if self.server_state == ComboFighter.state.in_round:
			emit('round_start', {'name':cname, 'state':self.server_state.value, 'prompts':self.prompts_list, 'scoreboard':self.last_round_results_list, 'cround':self.round_number, 'trounds':self.num_rounds, 'time':int(self.next_event_time)-1})
		elif self.server_state == ComboFighter.state.round_end:
			emit('round_end', {'prompts':self.prompts_list, 'time':int(self.next_event_time)-1, 'scoreboard':self.results_list, 'bestword':self.best_word_message, 'cround':self.round_number, 'trounds':self.num_rounds, 'winner':self.winners})
		elif self.server_state == ComboFighter.state.game_end:
			emit('game_end', {'time':int(self.next_event_time)-1,'results':self.results_list, 'winner':self.winners})
		elif self.server_state == ComboFighter.state.idle:
			pass
	
	def unregister_user(self):
		leave_room(self.room_name)
		uid = request.sid
		if self.player_registered(uid):
			user = self.get_user(uid=uid)
			if user.is_admin:
				if (self.num_admins() == 1 and len(self.users)>1):
					#Make the oldest non-admin an admin
					new_admin = None
					if user == self.users[0]:
						new_admin = self.users[1]
					else:
						new_admin = self.users[0]
					new_admin.is_admin = True
					emit('admin_change', {'name':new_admin.name, 'id':new_admin.uid, 'is_admin':True}, broadcast=True, room=self.room_name)
			for entry in self.results_list:
				if entry[0] == uid:
					self.results_list.remove(entry)
					break
			for entry in self.last_round_results_list:
				if entry[0] == uid:
					self.last_round_results_list.remove(entry)
					break
			emit('disconnect_message', {'name':user.name, 'id':user.uid}, broadcast=True, room=self.room_name)
			self.users.remove(user)

	def chat_message(self, message):
		emit('chat_message', {'id':request.sid, 'm':message, 'cname':self.get_user(uid=request.sid).name}, broadcast=True, room=self.room_name)
		error_message = "Error parsing chat message."
		auth = self.get_user(uid=request.sid).is_admin
		try:
			if message[0] == '!':
				parsed = message.split(" ")
				command = parsed[0]
				args = parsed[1:]
				if command == "!help":
					emit('system_message', 'Available commands: !help, !howToPlay, !players, !leave, !join, !check, !def, !promote, !demote, !setRoundTime, !setRoundEndTime, !setNumRounds, !setGameEndTime, !setNumPrompts, !setPromptDifficulty', broadcast=True, room=self.room_name)
				elif command == "!howToPlay":
					emit('system_message', "Your score for the round is equal to the sum of the values of prompts contained in your word times the number of prompts you use. Find words that use as many of the round's prompts as possible!", broadcast=True, room=self.room_name)
				elif command == "!players":
					emit('system_message', self.html_player_list(), broadcast=True, room=self.room_name)
				elif command == "!leave":
					requester = self.get_user(uid=request.sid)
					if not requester.in_game:
						error_message = "Error: You are already marked as AFK!"
						raise Exception(error_message)
					requester.in_game = False
					game_active = False
					for user in self.users:
						if user.in_game:
							game_active = True
							break
					self.game_active = game_active
					htmlclass = "user_name"
					if requester.is_admin:
						htmlclass+=" admin"
					emit('temp_leave_game', {'id':requester.uid, 'name':requester.name, 'msg':'<span class="'+htmlclass+'">'+requester.name + "</span> is now marked as AFK."}, broadcast=True, room=self.room_name)
				elif command == "!join":
					requester = self.get_user(uid=request.sid)
					if requester.in_game:
						error_message = "Error: You are not marked as AFK!"
						raise Exception(error_message)
					requester.in_game = True
					self.game_active = True
					htmlclass = "user_name"
					if requester.is_admin:
						htmlclass+=" admin"
					emit('temp_join_game', {'id':requester.uid, 'name':requester.name, 'msg':'<span class="'+htmlclass+'">'+requester.name + "</span> is no longer marked as AFK."}, broadcast=True, room=self.room_name)
				elif command == "!promote":
					if not auth:
						error_message = "Error: " + command + " can only be used by this room's admins."
						raise Exception(error_message)
					error_message = "Usage: !promote &lt;username&gt;"
					target = self.get_user(name=args[0])
					if not target:
						error_message = "Error: That user doesn't exist!"
						raise Exception(error_message)
					if target.is_admin:
						error_message="Error: <span class='user_name admin'>"+args[0]+"</span> is already an admin for this room."
						raise Exception(error_message)
					target.is_admin=True
					emit('admin_change', {'name':target.name, 'id':target.uid, 'is_admin':target.is_admin}, broadcast=True, room=self.room_name)
				elif command == "!demote":
					if not auth:
						error_message = "Error: " + command + " can only be used by this room's admins."
						raise Exception(error_message)
					error_message = "Usage: !demote &lt;username&gt;"
					target = self.get_user(name=args[0])
					if not target:
						error_message = "Error: That user doesn't exist!"
						raise Exception(error_message)
					if not target.is_admin:
						error_message="Error: <span class='user_name'>"+args[0]+"</span> is not an admin for this room."
						raise Exception(error_message)
					requester = self.get_user(uid=request.sid)
					if requester.register_time > target.register_time:
						error_message = "Error: Can't demote a user who's been in the room longer than you!"
						raise Exception(error_message)
					if len(self.admin_ids()) == 1:
						error_message = "Error: This room must have at least one admin."
						raise Exception(error_message)
					target.is_admin=False
					emit('admin_change', {'name':target.name, 'id':target.uid, 'is_admin':target.is_admin}, broadcast=True, room=self.room_name)
				elif command == "!check":
					error_message="Usage: !check &lt;word&gt;"
					word = args[0].lower()
					if word in dicotools.words_permissive:
						emit('system_message', word + ' is in the current dictionary.', broadcast=True, room=self.room_name)
					else:
						emit('system_message', word + ' is not in the current dictionary.', broadcast=True, room=self.room_name)
				elif command == "!def":
					error_message="Usage: !def &lt;word(s)&gt;"
					# emit('system_message', "Retrieving definition. Please wait a few moments...", broadcast=True, room=self.room_name)
					emit('system_message', "The !def command is currently unavailable. Please try again later.", broadcast=True, room=self.room_name)
					self.socketio.start_background_task(target=chattools.fetch_and_send_defn, word=" ".join(args), socketio=self.socketio, msg_type="system_message", room=self.room_name)
				elif command == "!setRoundTime":
					if not auth:
						error_message = "Error: " + command + " can only be used by this room's admins."
						raise(error_message)
					error_message="Error: Round time must be between 5 and 300."
					t = int(args[0])
					if (t >= 5 and t <= 300):
						self.round_time = t
						emit('system_message', 'The round time has been set to '+str(t)+' starting next round.', broadcast=True, room=self.room_name)
					else:
						emit('system_message', error_message, broadcast=True, room=self.room_name)
				elif command == "!setRoundEndTime":
					if not auth:
						error_message = "Error: " + command + " can only be used by this room's admins."
						raise(error_message)
					error_message="Error: Round end time must be between 3 and 30."
					t = int(args[0])
					if (t >= 3 and t <= 30):
						self.round_results_time = t
						emit('system_message', 'The round end time has been set to '+str(t)+' starting next round.', broadcast=True, room=self.room_name)
					else:
						emit('system_message', error_message, broadcast=True, room=self.room_name)
				elif command == "!setNumRounds":
					if not auth:
						error_message = "Error: " + command + " can only be used by this room's admins."
						raise(error_message)
					error_message="Error: Number of rounds must be between 1 and 100."
					n = int(args[0])
					if (n >= 1 and n <= 100):
						self.num_rounds = n
						emit('system_message', 'The number of rounds has been set to '+str(n)+'.', broadcast=True, room=self.room_name)
					else:
						emit('system_message', error_message, broadcast=True, room=self.room_name)
				elif command == "!setGameEndTime":
					if not auth:
						error_message = "Error: " + command + " can only be used by this room's admins."
						raise(error_message)
					error_message="Error: Game end time must be between 3 and 40."
					t = int(args[0])
					if (t >= 3 and t <= 40):
						self.game_results_time = t
						emit('system_message', 'The game end time has been set to '+str(t)+'.', broadcast=True, room=self.room_name)
					else:
						emit('system_message', error_message, broadcast=True, room=self.room_name)
				elif command == "!setNumPrompts":
					if not auth:
						error_message = "Error: " + command + " can only be used by this room's admins."
						raise(error_message)
					error_message="Error: Number of prompts must be between 1 and 20."
					n = int(args[0])
					if (n >= 1 and n <= 20):
						self.num_prompts = n
						emit('system_message', 'The number of prompts has been set to '+str(n)+'.', broadcast=True, room=self.room_name)
					else:
						emit('system_message', error_message, broadcast=True, room=self.room_name)
				elif command == "!setPromptDifficulty":
					if not auth:
						error_message = "Error: " + command + " can only be used by this room's admins."
						raise(error_message)
					error_message="Error: Difficulty must be between 0 and 10. (Default is 3.5)"
					n = float(args[0])
					if (n >= 0 and n <= 10):
						self.prompt_difficulty = n
						emit('system_message', 'The prompt difficulty has been set to '+str(n)+'.', broadcast=True, room=self.room_name)
					else:
						emit('system_message', error_message, broadcast=True, room=self.room_name)
		except:
			#raise
			# print "emitting system message: " + error_message
			emit('system_message', error_message, broadcast=True, room=self.room_name)
			#e = sys.exc_info()[0]

	def eval_submission(self, message):
		user = self.get_user(uid=request.sid)
		message = message.strip().lower()
		# print "received " + message + " from user " + user.name
		if len(message)>30:
			message=message[:30]
		pretty_score_message, score = dicotools.pretty_score(self.prompts_list, message)
		# print "score: " + pretty_score_message
		#this is a bad way of doing this but not like i expect more than 2 people to be on my server ever
		for entry in self.results_list:
			if entry[0] == request.sid:
				if entry[2] == -1:
					entry[2] = message
					entry[3] = score
					entry[4] += score
		emit('gameplay_response', {'score':score, 'msg':pretty_score_message})
		emit('ready_user', request.sid, broadcast=True, room=self.room_name)
		#print "results list: " + str(self.results_list)
		#for user in self.users:
		#	print "user: " + user.name + ", " + str(user.in_game)
		for entry in self.results_list:
			user = self.get_user(uid=entry[0])
			if user.in_game and entry[2] == -1:
				return
		self.all_players_submitted = True

	def start_round(self):
		self.server_state = ComboFighter.state.in_round
		self.prompts_list = []
		prompts = []
		self.all_players_submitted = False
		self.best_word_message = "Server error: couldn't find the best word!"

		#clear last round's results
		for entry in self.results_list:
			entry[2] = -1
			entry[3] = 0

		while (len(prompts) != self.num_prompts):
			p = dicotools.rand_prompt(difficulty=self.prompt_difficulty)
			valid = True
			for prompt in prompts:
				if p in prompt or prompt in p:
					valid = False
					break
			if valid:			
				prompts.append(p)
		for p in prompts:
			p_value = dicotools.prompt_value(dicotools.counts[p])
			p_value += (random.random()-0.5)*(1/3.0)*p_value
			p_value = int(round(p_value))
			self.prompts_list.append((p, p_value))
			
		self.prompts_list = sorted(self.prompts_list, key=itemgetter(1))
		self.next_event_time = self.round_time
		# print self.room_name + " starting round " +str(self.round_number)+"/"+str(self.num_rounds)+" with prompts: "+str(self.prompts_list)
		self.socketio.emit('round_start', {'prompts':self.prompts_list, 'time':self.next_event_time-1, 'cround':self.round_number, 'trounds':self.num_rounds}, room=self.room_name) #take off 1 second to account for lag?

		self.socketio.start_background_task(target=self.prepare_best_word)
		while (self.next_event_time > 0):
			if len(self.users) == 0:
				self.room_active = False
				return
			if not self.game_active:
				self.next_state = self.idle
				return
			if self.all_players_submitted:
				break
			self.socketio.sleep(0.1)
			self.next_event_time -= 0.1
		self.next_state = self.end_round

	def end_round(self):
		self.server_state = ComboFighter.state.round_end
		high_score=max(self.results_list, key=itemgetter(3))[3]
		self.winners = [elt[1] for elt in self.results_list if elt[3]==high_score and high_score>0]
		# print "high score is: " + str(high_score) + ", winners are: " + str(self.winners)
		self.results_list = sorted(self.results_list, key=itemgetter(4), reverse=True)
		self.last_round_results_list = copy.deepcopy(self.results_list)
		# print "results for the round: " + str(self.results_list)
		self.next_event_time = self.round_results_time
		self.socketio.emit('round_end', {'prompts':self.prompts_list, 'time':self.next_event_time-1, 'scoreboard':self.results_list, 'bestword':self.best_word_message, 'cround':self.round_number, 'trounds':self.num_rounds, 'winner':self.winners}, room=self.room_name) #take off 1 second to account for lag?
		while (self.next_event_time > 0):
			if len(self.users) == 0:
				self.room_active = False
				return
			if not self.game_active:
				self.next_state = self.idle
				return
			self.socketio.sleep(1)
			self.next_event_time -= 1
		if self.round_number >= self.num_rounds:
			self.next_state = self.end_game
		else:
			self.round_number += 1
			self.next_state = self.start_round

	def start_game(self):
		self.server_state = ComboFighter.state.game_start
		if len(self.users) == 0:
			self.room_active = False
			return
		self.round_number = 1
		# print "Starting new game at " +self.room_name
		self.results_list = []
		for user in self.users:
			self.results_list.append([user.uid, user.name, -1, 0, 0])
		self.last_round_results_list = copy.deepcopy(self.results_list)
		self.next_state = self.start_round

	def end_game(self):
		if len(self.results_list) > 0:
			print(self.results_list[0][1] + " wins!")
		self.next_event_time = self.game_results_time
		high_score=max(self.results_list, key=itemgetter(4))[4]
		self.winners = [elt[1] for elt in self.results_list if elt[4]==high_score and high_score>0]
		# print "high score is: " + str(high_score) + ", winners are: " + str(self.winners)
		self.socketio.emit('game_end', {'time':self.next_event_time-1,'results':self.results_list, 'winner':self.winners}, room=self.room_name)
		while (self.next_event_time > 0):
			if len(self.users) == 0:
				self.room_active = False
				return
			if not self.game_active:
				self.next_state = self.idle
				return
			self.socketio.sleep(1)
			self.next_event_time -= 1
		self.next_state = self.start_game

	def setup(self):
		#When we're first setting up the room, wait for players to load.
		wait_time=10
		players_ready = False
		while (wait_time >= 0):
			if len(self.users)>0:
				players_ready = True
				break
			self.socketio.sleep(0.1)
			wait_time-=0.1
		if not players_ready:
			self.room_active = False
		self.main()
		
	def main(self):
		while (self.room_active):
			self.next_state()
		self.teardown()

	def idle(self):
		self.server_state = ComboFighter.state.idle
		# print self.room_name + " is now idling."
		self.socketio.emit('idle', {'msg':"Waiting for players to join."}, room=self.room_name)
		while not self.game_active:
			if len(self.users)==0:
				self.room_active = False
				return
			self.socketio.sleep(0.1)
		self.next_state = self.start_game

	def teardown(self):
		self.index_lock.acquire()
		del self.index[self.room_name]
		self.index_lock.release()
		# print self.room_name + ": No more users remaining. Shutting down."

	def prepare_best_word(self):
		best_word = dicotools.combofighter_solver(self.prompts_list)
		score, hit = dicotools.comboscore(self.prompts_list, best_word)
		self.best_word_message = "The best possible word was " + best_word.upper() + ", which scores a whopping " + str(score) + " points, and hits the following prompts: " + ', '.join([a.upper() for a in hit[0]])
		

	def handle_event(self, event, *args):
		# print "ComboFighter instance at " + self.room_name + " handling " + event + " by " + request.sid +  "  with params: " + str(args)
		#server side events: 'connect disconnect chat_message gameplay_user_submit join_game leave_game'
		if event == self.server_events.connect.name:
			self.register_user()
		elif event == self.server_events.disconnect.name:
			self.unregister_user()
		elif event == self.server_events.chat_message.name:
			self.chat_message(args[0])
		elif event == self.server_events.gameplay_user_submit.name:
			self.eval_submission(args[0])
		elif event == self.server_events.join_game.name:
			self.join_game(args[0])
		elif event == self.server_events.leave_game.name:
			self.leave_game(args[0])
		else:
			print("Error: Room " + self.room_name + " received a request it can't handle!")

class User:
	def __init__(self, uid, name=None, in_game=True, is_admin=False):
		self.uid = uid
		if (name==None):
			self.name=dicotools.get_random_word()
		self.in_game=in_game
		self.is_admin=is_admin
		self.register_time = time.time()


    
