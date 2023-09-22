import random
import math
import unicodedata
import codecs
import string
from threading import Timer
from operator import itemgetter

dico_american = codecs.open("app/static/data/american-english", encoding='utf-8')
dico_british = codecs.open("app/static/data/british-english", encoding='utf-8')
dico_pseudo = codecs.open("app/static/data/english_pseudo.txt", encoding='utf-8')


words = set() #"standard" dico from which we draw prompts and decide on prompt values
counts = {}
prompt2word = {}
words_permissive=set() #permissive dico against which we check prompts


# TODO: why am i encoding and decoding things here?
for line in dico_american:
	if '\'' not in line and line[0].islower():
		word = unicodedata.normalize('NFKD', line).encode('ascii', 'ignore')
		word = word.strip()
		word = word.lower()
		word = word.decode("utf-8")
		words.add(word)
		words_permissive.add(word)

for line in dico_british:
	if '\'' not in line and line[0].islower():
		word = unicodedata.normalize('NFKD', line).encode('ascii', 'ignore')
		word = word.strip()
		word = word.lower()
		word = word.decode("utf-8")
		if word not in words:
			words.add(word)
			words_permissive.add(word)

for line in dico_pseudo:
	if '\'' not in line and line[0].islower():
		word = unicodedata.normalize('NFKD', line).encode('ascii', 'ignore')
		word = word.strip()
		word = word.lower()
		word = word.decode("utf-8")
		if word not in words_permissive:
			words_permissive.add(word)
		

for word in words:
	
	#length 2 window
	for i in range(len(word)-1):
	    pair = word[i:i+2]
	    if len(pair) != 2:
	        print(word)
	        break
	    if pair in counts:
	        counts[pair]+=1
	        prompt2word[pair].add(word)
	    else:
	        counts[pair]=1
	        solves = set()
	        solves.add(word)
	        prompt2word[pair]=solves
	#length 3 window
	for i in range(len(word)-2):
	    trip = word[i:i+3]
	    if len(trip)!=3:
	        print(word)
	        break
	    if trip in counts:
	        counts[trip]+=1
	        prompt2word[trip].add(word)
	    else:
	        counts[trip]=1
	        solves = set()
	        solves.add(word)
	        prompt2word[trip]=solves

c_words = sorted(counts,key=counts.get,reverse=True)
c_vals = sorted(counts.values(),reverse=True)
cum_c_vals = [sum(c_vals[0:i]) for i in range(1,len(c_vals)+1)]

def get_random_word():
	# TODO: why does this require a conversion to a list?
	return random.sample(list(words),1)[0]

def find_closest(l,n):
	imax = len(l)-1
	imin = 0
	while ((imax - imin)!=1):
		#print imin, imax
		# i = (imax+imin)/2
		i = (imax+imin)//2
		if l[i]<n:
			imin=i
		elif l[i]>n:
			imax=i
		elif l[i]==n:
			return i,l[i]
	return imax, l[imax]

def rand_prompt(difficulty=(10.0/6.0)):
	#rand_n = int(math.floor(random.triangular(1, cum_c_vals[-1], cum_c_vals[-1]*(difficulty/10.0))))
	#make stdev small near the edges
	stdev = None
	if difficulty<=5:
		stdev = 0.1 + difficulty*0.06
	else:
		stdev = 0.4 - (difficulty-5)*0.06
	rand_n = reflected_normal_int((difficulty/10.0), stdev, 1, cum_c_vals[-1])
	index, value = find_closest(cum_c_vals, rand_n)
	return c_words[index]

#Restricts an input to the [0,1] range, giving its value according to a sawtooth wave
def reflection(n):
	frac, whole = math.modf(n)
	if math.floor(int(n))%2 == 0:
		return math.fabs(frac)
	else:
		return 1-math.fabs(frac)

#mode and stdev should be suitable to a distribution in [0,1]. That distribution is then scaled to [minbound, maxbound] and a value is sampled from it, using reflection rules if the output goes past the bounds.
def reflected_normal_int(mode, stdev, minbound, maxbound):
	n = reflection(random.normalvariate(mode, stdev))
	return minbound + int((maxbound - minbound)*n)

#n is number of solves available for a prompt
def prompt_value(n):
    return int(math.floor((12.0/math.log(n+1, 10))/(1.0/3.0 + n*(1.0/14000.0))))

def comboscore(prompts_list, word):
    n = 0
    nval = 0
    prompts_hit = []
    results = []
    value_string = ""
    number_string = ""
    for prompt, value in prompts_list:
        if prompt in word:
            n+=1
            nval += value
            prompts_hit.append(prompt)
            value_string += " + " + str(value)
    results_string = "("+value_string[3:]+") x " + str(n)
    results.append(prompts_hit)
    results.append(results_string)
    return n*nval, results

def pretty_score(prompts_list, response):
	if response not in words_permissive:
		return "Your word, " + response.upper() + ", is not in the dictionary.", 0
	score, hit = comboscore(prompts_list, response)
	return "Your word was: " + response.upper() + ", scoring " + hit[1] + " = " + str(score) + " points! You hit the following prompts: " + ', '.join([a.upper() for a in hit[0]]) + ".", score

def combofighter_solver(prompts_list):
    max_points = 0
    max_word = None
    for word in words_permissive:
        score, hit = comboscore(prompts_list, word)
        if score > max_points:
            max_points = score
            max_word = word
    return max_word

def tuplify(s):
    e = s.split(" ")
    l =  [tuple(e[2*i:2*i+2]) for i in range(len(e)/2)]
    f = [(x[0], int(x[1])) for x in l]
    return f

#can't believe there is no built-in for this...
def all_letters(word):
	return all([x in string.ascii_letters for x in word])

#because is_alpha() is locale dependent, for some weird reason
def all_letters_or_numbers(word):
	return all([x in string.ascii_letters+string.digits for x in word])

#should just use a regex at this point
def all_letters_or_numbers_or_underscores(word):
	return all([x in string.ascii_letters+string.digits+"_" for x in word])

def random_lab_title():
	Sparklin = ["pseudo", "blinding", "sparkling","bright","star","brilliant","gleaming","glowing","scintillating","shimmering","shining","radiant", "glinting", "effulgent"]
	Labs = ["labs", "workshops", "hubs", "groups", "centers", "associations", "bands", "bodies", "organizations", "assemblies"]
	Bomb = ["pseudo", "bomb", "shockwave", "explosive", "explosion", "mortar", "h-bomb", "blast", "mine", "missile", "projectile", "rocket", "torpedo", "bombshell", "dynamite", "c4", "grenade", "shell"]
	Party = ["party", "celebration", "amusement", "diversion", "entertainment", "feast", "festivity", "fete", "gala", "social", "reception", "sortie", "rendezvous"]
	return "Welcome to "+random.choice(Sparklin).capitalize()+" "+random.choice(Labs).capitalize()+"' "+random.choice(Bomb).capitalize()+" "+random.choice(Party).capitalize()+"!"




		







            
