import sys
import re
import csv
sys.path.append(sys.path[0] + "/../lib")
from util import conn_3312

def get_lemma_langs (row):
	res = []
	for lemma in row["Lemmata"]:
		if not lemma["Sprache"] in res:
			res.append(lemma["Sprache"])
	return res

def only_langs (row, langs):
	langs_in_row = get_lemma_langs(row)
	
	if len(langs) != len(langs_in_row):
		return False
		
	for lang in langs:
		if not lang in langs_in_row:
			return False
	
	return True
	
def get_lemma_orth (row, lang):

	forms = []
	for lemma in row["Lemmata"]:
		if lemma["Sprache"] == lang and lemma["Subvocem"] not in forms:
			forms.append(lemma["Subvocem"])
	
	if len(forms) > 1:
		raise Exception("Multiple forms for lemma for lang " + lang + ": " + str(forms))
		
	ret = forms[0]
	
	if not re.match(r"^[\w '-\-]*$", ret):
		raise Exception("Non-letters in lemma: " + ret)
		
	return ret
	
def split_orth (orth):
	if not re.match(r"^(\w|[ '-\-])+ / (\w|[ '-\-])+$", orth):
		raise Exception("Cannot split " + orth)
		
	return orth.split(" / ")
	
def check_roa_orth (orth):
	if not re.match(r"^(\w|[ '-\-])+$", orth):
		raise Exception("Non-letters in lemma for single lexem: " + orth)
	
	return orth
		

if __name__ == "__main__":
	conn = conn_3312("va_xxx")

	with conn.cursor() as cur:
		sql = """
		SELECT DISTINCT Id_morph_Typ, Orth, mt.Sprache AS MSprache, Wortart, Genus, x.Sprache AS BSprache, Subvocem, Abkuerzung
		FROM morph_typen mt 
			LEFT JOIN 
				(SELECT ID_morph_Typ, Sprache, Subvocem, Abkuerzung 
					FROM vtbl_morph_typ_lemma vmtl
						JOIN lemmata l USING (Id_Lemma)
						JOIN bibliographie b ON Abkuerzung = l.Quelle
				WHERE Subvocem != '<vacat>' AND Abkuerzung != 'VA') x USING (Id_morph_Typ)
		WHERE mt.Quelle = 'VA' AND mt.Wortart != 'Satz' AND mt.Orth != 'IGNORE' AND mt.Orth NOT LIKE '%2' AND ID_morph_Typ IN (38987,38164,7137,5278,3237,4004,27446,17504,10296,1746,52865,9562,29100,52735,23722,43093,4086,26826,30968,46809)
		ORDER BY ID_morph_Typ ASC"""
		
		idm = False
		cur.execute(sql)
		data_gr = {}
		lemmata = []
		prev = []
		
		for row in cur.fetchall():
			if idm != row[0]:
				if idm != False:
					data_gr[idm] = {
						"Orth" : prev[1],
						"Sprache" : prev[2],
						"Wortart" : prev[3],
						"Genus" : prev[4],
						"Lemmata" : lemmata
					}
					lemmata = []
					
				idm = row[0]
			if row[6] and not row[5]:
				raise Exception("No lang for source " + row[7])
			if row[6]:
				if row[2] != "gem" or row[5] in ("deu", "bar"):
					sv = row[6]
					
					if row[7] == "DRG":
						sv = sv.lower()
						if sv.endswith(" i"):
							sv = sv[0:-2]
						if sv.endswith(" ii"):
							sv = sv[0:-3]
						if sv.endswith(" iii"):
							sv = sv[0:-4]
				
					lemmata.append({
						"Sprache" : row[5],
						"Subvocem" : sv
					})
			prev = row
			
		data_gr[idm] = {
			"Orth" : prev[1],
			"Sprache" : prev[2],
			"Wortart" : prev[3],
			"Genus" : prev[4],
			"Lemmata" : lemmata
		}
		
		res = []
		roaWithoutLemma = []
		deuWithoutLemma = []
		itFrWithOneForm = []
		invalidita = []
		invalidfra = []
		invalidlld = []
		invalidroh = []
		invalidbar = []
		
		for key in data_gr:
			row = data_gr[key]
			if row["Sprache"] == "sla":
				res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "slv", row["Orth"]])
			elif row["Sprache"] == "gem" and (len(row["Lemmata"]) == 0 or only_langs(row, ["deu"])):
				if len(row["Lemmata"]) == 0:
					deuWithoutLemma.append([key, row["Orth"]])
				else:
					res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "deu", row["Orth"]])
			elif row["Sprache"] == "gem" and only_langs(row, ["bar"]):
				res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "bar", row["Orth"]])
			elif row["Sprache"] == "gem" and only_langs(row, ["deu", "bar"]):
				res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "deu", row["Orth"]])
				try:
					res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "bar", get_lemma_orth(row, "bar")])
				except Exception as e:
					invalidbar.append(e)
			elif row["Sprache"] == "roa":
				langs = get_lemma_langs(row)
				
				try:
					(fra, ita) = split_orth(row["Orth"])
					
					if only_langs(row, ["lld", "roh"]):
						res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "lld", fra])
						res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "roh", ita])
						langs = []
					else:
						res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "fra", fra])
						res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "ita", ita])
						
						if "ita" in langs:
							langs.remove("ita")
						if "fra" in langs:
							langs.remove("fra")
				except:
					if len(langs) == 0:
						#roaWithoutLemma.append([key, row["Orth"]])
						res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "ita", row["Orth"]])
						continue
				
				if "ita" in langs and "fra" in langs:
					try:
						(fra, ita) = split_orth(row["Orth"])
						res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "fra", fra])
						res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "ita", ita])
						langs.remove("fra")
						langs.remove("ita")
					except:
						itFrWithOneForm.append([key, row["Orth"]])
				
				if "ita" in langs:
					try:
						res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "ita", check_roa_orth(row["Orth"])])
					except Exception as e:
						invalidita.append(e)
					
				if "fra" in langs:
					try:
						res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "fra", check_roa_orth(row["Orth"])])
					except Exception as e:
						invalidfra.append(e)
					
				if "lld" in langs:
					try:
						res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "lld", get_lemma_orth(row, "lld")])
					except Exception as e:
						invalidlld.append(e)
					
				if "roh" in langs:
					try:
						res.append([key, row["Orth"], row["Sprache"], row["Genus"], row["Wortart"], "roh", get_lemma_orth(row, "roh")])
					except Exception as e:
						invalidroh.append(e)
			else:
				raise Exception("Cannot handle " + str(row))
			
		with open("errors.txt", "w", encoding="utf8") as errorFile:
			print("Roa without lemma", file=errorFile)
			for x in roaWithoutLemma:
				print(x, file=errorFile)
			print("\n", file=errorFile)

			print("Deu without lemma", file=errorFile)
			for x in deuWithoutLemma:
				print(x, file=errorFile)
			print("\n", file=errorFile)
			
			print("Roa with it/fr but no slash", file=errorFile)
			for x in itFrWithOneForm:
				print(x, file=errorFile)
			print("\n", file=errorFile)
			
			print("Invalid ita", file=errorFile)
			for x in invalidita:
				print(x, file=errorFile)
			print("\n", file=errorFile)
			
			print("Invalid fra", file=errorFile)
			for x in invalidfra:
				print(x, file=errorFile)
			print("\n", file=errorFile)
			
			print("Invalid lld", file=errorFile)
			for x in invalidlld:
				print(x, file=errorFile)
			print("\n", file=errorFile)
			
			print("Invalid roh", file=errorFile)
			for x in invalidroh:
				print(x, file=errorFile)
			print("\n", file=errorFile)
			
			print("Invalid bar", file=errorFile)
			for x in invalidbar:
				print(x, file=errorFile)
			print("\n", file=errorFile)
				
		with open("res.csv", "w", encoding="utf8", newline="") as resFile:
			csvwriter = csv.writer(resFile)
			csvwriter.writerow(["ID", "Orth", "Sprachfamilie", "Genus", "Wortart", "Sprache Wikidata", "Lexem Wikidata"])
			last_id = False
			for row in res:
				if row[0] == last_id:
					csvwriter.writerow(["", "", "", "", "", row[5], row[6]])
				else:
					csvwriter.writerow(row)
				last_id = row[0]
		