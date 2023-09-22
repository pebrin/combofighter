# from wordnik import *
# apiUrl = 'http://api.wordnik.com/v4'
# apiKey = None #redacted -- ideally this would be in a top-level gitignored config file
# client = swagger.ApiClient(apiKey, apiUrl)
# wordApi = WordApi.WordApi(client)
#
# def get_defn(word):
# 	# print "Started fetching definition for " + word
# 	pronunciations = wordApi.getTextPronunciations(word, limit=1, useCanonical=True)
# 	definitions = wordApi.getDefinitions(word, limit=3, useCanonical=True)
# 	if not definitions:
# 		return "Couldn't find a dictionary entry for " + word + "."
# 	defn = ""
# 	pron = ""
# 	if pronunciations and pronunciations[0].rawType!="arpabet":
# 		pron = pronunciations[0].raw
# 	defn+= "<b>"+definitions[0].word + "</b> " + pron + "\n "
# 	if len(definitions) > 1:
# 		defn+= "Top "+str(len(definitions))+" definitions:\n "
# 	for i, d in enumerate(definitions):
# 		text = ""
# 		if (d.text):
# 			text = d.text
# 		if (d.partOfSpeech):
# 			defn+=str(i+1)+": "+d.partOfSpeech + ". " + text+"\n "
# 			pos = d.partOfSpeech
# 		else:
# 			defn+=str(i+1)+": "+ text+"\n "
# 	return defn[:-2]
#
# def fetch_and_send_defn(word, msg_type, socketio, room):
# 	try:
# 		d = get_defn(word)
# 		d = d.replace('\n', '<br/>')
# 		socketio.emit(msg_type, d, broadcast=True, room=room)
# 	except:
# 		socketio.emit(msg_type, "There was an error with your request. Try again later.", broadcast=True, room=room)

def get_defn(word):
	pass

def fetch_and_send_defn(word, msg_type, socketio, room):
	pass
