#coding:utf-8

from flask import Flask, render_template, send_from_directory, request, make_response, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from combofighter import ComboFighter
from operator import itemgetter
from threading import Lock

import eventlet
eventlet.monkey_patch()

import threading
import os
import signal
import sys
import string
import dicotools

app = Flask(__name__)
app.config['SECRET_KEY'] = None #redacted
socketio = SocketIO(app)

rooms = {}
rooms_lock = Lock()
active_event_types = [event.name for event in ComboFighter.server_events]


@app.route('/')
def main():
	sorted_games = sorted(rooms.values(), key=lambda x:len(x.users), reverse=True)
	return render_template('index.html', data={'games':sorted_games, 'title':dicotools.random_lab_title(), 'url':url_for('spawn_game', game_name="", _external=True, _scheme='https')})

#Treat socket.io separately -- want users to cache it.
@app.route('/js/socket.io.js')
def send_socket_js():
	return send_from_directory(os.getcwd()+'/app/static/js', 'socket.io.js')

@app.route('/js/<string:js_file>.js')
def send_js(js_file):
	r = make_response(send_from_directory(os.getcwd()+'/app/static/js', js_file+'.js'))
	r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
	r.headers["Pragma"] = "no-cache"
	return r

@app.route('/css/<string:css_file>.css')
def send_css(css_file):
	r = make_response(send_from_directory(os.getcwd()+'/app/static/css', css_file+'.css'))
	r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
	r.headers["Pragma"] = "no-cache"
	return r

@app.route('/sounds/<audio_file>')
def send_audio(audio_file):
	return send_from_directory(os.getcwd()+'/app/static/audio', audio_file)

@app.route('/images/<image_file>')
def send_image(image_file):
	return send_from_directory(os.getcwd()+'/app/static/images', image_file)

@app.route('/game/combofighter/<string:game_name>')
def spawn_game(game_name):
	if not dicotools.all_letters_or_numbers_or_underscores(game_name) or not len(game_name)<=30:
		return game_name + " is not a valid name!", 400
	# room_name=request.base_url
	room_name=request.url
	if room_name not in rooms:
		print("Creating new ComboFighter instance at " + room_name)
		game = ComboFighter(app=app, index_entry=(rooms, rooms_lock), room_name=room_name, game_name=game_name, socketio=socketio)
		rooms[room_name] = game
		socketio.start_background_task(target=game.setup)
		return render_template('combofighter.html', data=game.defaults)
	return render_template('combofighter.html', data=rooms[room_name].defaults)

def create_event_router(event):
	def event_router(*args):
		try:
			#reminder: this is somewhat sketchy
			room_name = request.headers['referer']			
			if room_name in rooms:
				rooms[room_name].handle_event(event, *args)
			else:
				print("Ignoring event " + event + " in room " + room_name + " by user " + request.sid + " - room doesn't exist!")
		except:
			print("Error in handling event. Aborting...")
			e_type, e_value, e_traceback = sys.exc_info()
			print(e_type)
			print(e_value)
			print(e_traceback)
			raise
	return event_router

if __name__ == "__main__":
	def signal_handler(signum, frame):
		socketio.emit("system_message", "Alert: This server is restarting soon. Your game will be interrupted. Please wait a minute or two and then try rejoining.")
	signal.signal(signal.SIGTERM, signal_handler)
		
	for event in active_event_types:
		router = create_event_router(event)
		socketio.on_event(event, router)
	port = int(os.environ.get("PORT", 5000))
	socketio.run(app, host='0.0.0.0', port=port)
