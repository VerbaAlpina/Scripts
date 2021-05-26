import pymysql
import re
from functools import reduce
import sys
sys.path.append(sys.path[0] + "/../lib")
from util import conn_3312

drg_informants = {}
invalid = []
last_letter = None

def add_pair (number, spor, explicit, ortsangabe, cur):
	#print ((number, ortsangabe))

	if number in drg_informants:
		id = drg_informants[number]
	else:
		if re.match("^[ECS][1-9][0-9]$", number):
			sql = "INSERT INTO va_xxx.Informanten (Erhebung, Nummer, Sprache, Ortsname, Bemerkungen) VALUES ('DRG', %s, 'rom', '???', '')"
			cur.execute(sql, number)
			id = cur.lastrowid
			drg_informants[number] = id
		else:
			raise Exception("Invalid informant number: " + number)
			
		
		
	sql = "INSERT IGNORE INTO pva_drg.vtbl_formen_informanten (id_form, id_informant, spor, explicit) SELECT id_form, %s, %s, %s FROM pva_drg.phon_formen WHERE Ortsangabe = %s"
	cur.execute(sql, (id, spor, explicit, ortsangabe))
	
def resolve_loc (ortsangabe, explicit_last_letter = None):
	global last_letter
	print(ortsangabe)
	
	if ortsangabe.startswith("Nur bezeugt für "):
		ortsangabe = ortsangabe[16:]
	
	if ortsangabe.startswith("nur ") or ortsangabe.startswith("Nur "):
		ortsangabe = ortsangabe[4:]
	
	if ortsangabe.startswith("in ") or ortsangabe.startswith("In "):
		ortsangabe = ortsangabe[3:]
		
	#Escape separators in brackets
	ortsangabe_neu = ""
	in_bracket = False
	for index, letter in enumerate(ortsangabe):
		if letter == "(":
			in_bracket = True
		if letter == ")":
			in_bracket = False
			
		if in_bracket and letter == "," and ortsangabe[index-1] != "#":
			ortsangabe_neu += "#,"
		elif in_bracket and index + 4 < len(ortsangabe) and ortsangabe[index:index+4] == " und" and ortsangabe[index-1] != "#":
			ortsangabe_neu += "# "
		else:
			ortsangabe_neu += letter
			
	ortsangabe = ortsangabe_neu

	ll = explicit_last_letter if explicit_last_letter else last_letter

	spor = False

	res = []
	if re.search("(?<!#)(?:, | und )", ortsangabe):
		if not explicit_last_letter:
			last_letter = None
		
		for part in re.split("(?<!#)(?:, | und )", ortsangabe):
			sub = resolve_loc(part, explicit_last_letter)
			
			if sub:
				res += sub
			else:
				last_letter = None
				return None
		
		if not explicit_last_letter:
			last_letter = None
		return res
	
	if ortsangabe.endswith(" spor."):
		ortsangabe = ortsangabe[0:-6]
		spor = True
		
	if ortsangabe.startswith("spor. "):
		ortsangabe = ortsangabe[6:]
		spor = True
	
	#E 3
	if re.match("^[ECS] [0-9]$", ortsangabe):
		last_letter = ortsangabe[0]
		return [(number, spor, False) for number in drg_informants.keys() if number.startswith(ortsangabe.replace(" ", ""))]
	# E 30
	if re.match("^[ECS] [0-9]{2}$", ortsangabe):
		last_letter = ortsangabe[0]
		return [(ortsangabe.replace(" ", ""), spor, True)]
	# E 31-44
	elif re.match("^[ECS] [0-9]{2}–[0-9]{2}$", ortsangabe):
		letter = ortsangabe[0]
		last_letter = letter
		posDash = ortsangabe.find("–")
		start = int(ortsangabe[2:posDash])
		end = int(ortsangabe[posDash + 1:])
		
		return [(letter + str(start), spor, True)] + [(number, spor, False) for number in drg_informants.keys() if number > letter + str(start) and number < letter + str(end)] +  [(letter + str(end), spor, True)]
	# E 1-3
	elif re.match("^[ECS] [0-9]–[0-9]$", ortsangabe):
		letter = ortsangabe[0]
		last_letter = letter
		start = int(ortsangabe[2])
		end = int(ortsangabe[4])
		
		return map(lambda x: (x[0], spor, False), reduce(lambda x, y: x + y, map(resolve_loc, [letter + " " + str(i) for i in range(start, end + 1)])))
		
	# E 1-24
	elif re.match("^[ECS] [0-9]–[0-9]{2}$", ortsangabe):
		letter = ortsangabe[0]
		last_letter = letter
		start = int(ortsangabe[2])
		end = ortsangabe[4:6]
		
		if int(end[0]) > start:
			complete_ranges = map(lambda x: (x[0], spor, False), reduce(lambda x, y: x + y, map(resolve_loc, [letter + " " + str(i) for i in range(start, int(end[0]))])))
		else:
			complete_ranges = []
		if end[0] == "9":
			min_last = min([number for number in drg_informants.keys() if number > letter + end[0] and number.startswith(letter)])
		else:
			min_last = min([number for number in drg_informants.keys() if number > letter + end[0] and number < letter + str(int(end[0]) + 1)])
		
		return list(complete_ranges) + list(map(lambda x: (x[0], spor, x[2]), resolve_loc(letter + " " + min_last[1:] + "–" + end)))
	# E
	elif re.match("^[ECS]$", ortsangabe):
		last_letter = None
		return [(number, spor, False) for number in drg_informants.keys() if number.startswith(ortsangabe)]
	# 3
	elif ll and re.match("^[0-9]$", ortsangabe):
		return [(number, spor, False) for number in drg_informants.keys() if number.startswith(ll + ortsangabe)]
	# 30
	elif ll and re.match("^[0-9]{2}$", ortsangabe):
		return [(ll + ortsangabe, spor, True)]
	# 31-44
	elif ll and re.match("^[0-9]{2}–[0-9]{2}$", ortsangabe):
		posDash = ortsangabe.find("–")
		start = int(ortsangabe[0:posDash])
		end = int(ortsangabe[posDash + 1:])
		
		return [(ll + str(start), spor, True)] + [(number, spor, False) for number in drg_informants.keys() if number > ll + str(start) and number < ll + str(end)] +  [(ll + str(end), spor, True)]
	# 1-3
	elif ll and re.match("^[0-9]–[0-9]$", ortsangabe):
		start = int(ortsangabe[0])
		end = int(ortsangabe[2])

		return map(lambda x: (x[0], spor, False), reduce(lambda x, y: x + y, map(resolve_loc, [ll + " " + str(i) for i in range(start, end + 1)])))
	elif ortsangabe.find(" (ohne") != -1:
		pos = ortsangabe.find(" (ohne ")
		
		pos_str = ortsangabe[0: pos]
		positive = map(lambda x: (x[0], spor, x[2]), resolve_loc(pos_str))
		negative = resolve_loc(ortsangabe[pos + 7:-1].replace("#",""), pos_str if re.match("^[ECS]$", pos_str) else last_letter)
		
		res = []
		for p in positive:
			if p[0] not in map(lambda x: x[0], negative):
				res.append(p)
				
		return res
	else:
		invalid.append(ortsangabe)
		

if __name__ == "__main__":
	all_new = False

	conn = conn = conn_3312()

	with conn.cursor() as cur:
		sql = "SELECT Nummer, Id_Informant FROM va_xxx.Informanten WHERE Erhebung = 'DRG'"
		cur.execute(sql)
		for informant in cur.fetchall():
			drg_informants[informant[0]] = informant[1]
	
		if all_new:
			sql = "DELETE FROM pva_drg.vtbl_formen_informanten"
			cur.execute(sql)
		
		sql = "select distinct ortsangabe from pva_drg.phon_formen f"
		if not all_new:
			sql += " WHERE NOT exists (SELECT * from pva_drg.vtbl_formen_informanten v where v.Id_Form = f.Id_Form)"
		cur.execute(sql)
		
		for loc in cur.fetchall():
			numbers = resolve_loc(loc[0])
			
			if numbers:
				for number in numbers:
					add_pair(number[0], number[1], number[2], loc[0], cur)
				conn.commit()
				
		for ig in invalid:
			print ("Invalid location: " + ig)
		