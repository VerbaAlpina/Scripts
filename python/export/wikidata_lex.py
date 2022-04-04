# from wikibaseintegrator import wbi_core, wbi_login, wbi_datatype

# login_instance = wbi_login.Login(user='FZacherl', pwd='dosensepp')

# lexeme = wbi_datatype.Lexeme("L12439", "P5185")

# wd_item = wbi_core.ItemEngine(data=[lexeme])

# print(wd_item)

import LexData
import csv
import sys
sys.path.append(sys.path[0] + "/../lib")
from util import conn_3312

def pos_qid (pos):
	if pos == "sub":
		qid = 1084
	elif pos == "v":
		qid = 24905
	else:
		raise Exception("POS not connected to QID: " + pos)
		
	return "Q" + str(qid)
	
def gender_qid (gender):
	if gender == "m":
		qid = 499327
	elif gender == "f":
		qid = 1775415
	elif gender == "n":
		qid = 1775461
	else:
		raise Exception("Gender not connected to QID: " + gender)
		
	return "Q" + str(qid)
	
def wd_lang (iso3):
	if iso3 == "fra":
		return "fr"
	elif iso3 == "ita":
		return "it"
	elif iso3 == "deu":
		return "de"
	elif iso3 == "slv":
		return "sl"
	elif iso3 == "roh":
		return "rm"
		
	raise Exception("Lang not connected to wikidata lang abbreviation: " + iso3)
	

def add_lid_to_db (id_mtype, lid, lang, cur, conn):
	sql = "INSERT IGNORE INTO lids (Id_morph_Typ, LID, Sprache) VALUES (%s, %s, %s)"
	cur.execute(sql, (id_mtype, lid, lang))
	conn.commit()
	

repo = LexData.WikidataSession("FZacherl", "dosensepp")

conn = conn_3312("va_xxx")
with conn.cursor() as cur:
	with open("C:/Users/fz/Desktop/examples.csv", "r", encoding = "utf-8-sig") as csvfile:
		csvreader = csv.reader(csvfile, delimiter=',')
		for row in csvreader:
			lang = LexData.Language(wd_lang(row[2]), "Q" + row[3])
			pos = pos_qid(row[4])
			existing = LexData.search_lexemes(repo, row[1], lang, pos)
			
			if len(existing) > 0:
				if len(existing) == 1:
					print("Existing")
					lex = existing[0]
					add_lid_to_db(row[0], lex["id"][1:], row[2], cur, conn)
					
				else:
					print("Multiple")
			else:
				print ("Create", row[2], row[1])
				lex = LexData.create_lexeme(repo, row[1], lang, pos)
				print(lex)
				
				if row[5]:
					lex.addClaims({"P5185": [gender_qid(row[5])]})
					
				add_lid_to_db(row[0], lex["id"][1:], row[2], cur, conn)
			
