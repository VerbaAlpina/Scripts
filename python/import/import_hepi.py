import urllib.request
import urllib.parse
import json
import sys
sys.path.append(sys.path[0] + "/../lib")
from util import conn_3312
import xml.etree.ElementTree as ET

def update_locations (conn, headers, limit):
	api_url = "https://edh-www.adw.uni-heidelberg.de/data/api/geography/search?limit=" + str(limit)
	country_url = "https://edh-www.adw.uni-heidelberg.de/data/api/terms/country"

	with conn.cursor() as cur:

		#Update locations
		req = urllib.request.Request(country_url, headers=headers)
		response_data = urllib.request.urlopen(req)
		countries = json.loads(response_data.read())["countries"]
		
		for country_code in countries:
			num_geo = 0
			skipped = 0
			offset = 0
			
			print ("Country " + countries[country_code])
			
			sql = "SELECT edh_id, last_change FROM tools.epigraphik_heidelberg_orte WHERE country = %s"
			cur.execute(sql, (countries[country_code]))
			change_map = {}
			for row in cur.fetchall():
				change_map[row[0]] = row[1].strftime("%Y-%m-%d")
			
			while True:
				url = api_url + "&offset=" + str(offset) + "&country=" + country_code
				req = urllib.request.Request(url, headers=headers)
				
				response = urllib.request.urlopen(req)
				geo_data = json.loads(response.read())
				
				print("Got " + str(len(geo_data["items"])) + " items...")
				
				for row in geo_data["items"]:
					curr_id = int(row["id"])
					num_geo += 1
					
					if curr_id in change_map and change_map[curr_id] > row["last_update"]:
						skipped += 1
						continue

					if "coordinates" in row:
						lat, lng = row["coordinates"].split(",")	
						geo_string = "GeomFromText('POINT(" + str(lng) + " "  + str(lat) + ")')"
					else:
						geo_string = "NULL"
					
					name = ""
					if "find_spot" in row:
						name = row["find_spot"]
					
					name_anc = ""
					if "find_spot_ancient" in row:
						name_anc = row["find_spot_ancient"]
						
					name_mod = ""
					if "find_spot_modern" in row:
						name_mod = row["find_spot_modern"]
					
					
					prov = row["province"]
					country = row["country"]
					
					pid = None
					if "pleiades_uri" in row:
						url = row["pleiades_uri"]
						
						if not url.startswith("https://pleiades.stoa.org/places/"):
							raise Exception("Invalid pleiades url")
							
						pid = url[url.rindex("/") + 1:]
						
					gid = None
					if "geonames_uri" in row:
						url = row["geonames_uri"]
						
						if not url.startswith("https://www.geonames.org/"):
							raise Exception("Invalid geonames url: " + url)
							
						gid = url[url.rindex("/") + 1:]
					
					sql = """
						INSERT INTO tools.epigraphik_heidelberg_orte (edh_id, name, name_ancient, name_modern, province, country, pleiades_id, geonames_id, geo_data)
						VALUES (%s, %s, %s, %s, %s, %s, %s, %s, """ + geo_string + """)
						ON DUPLICATE KEY UPDATE
							name = %s, name_ancient = %s, name_modern = %s, province = %s, country = %s, pleiades_id = %s, geonames_id = %s, geo_data = """ + geo_string + """, last_change = CURRENT_TIMESTAMP
						"""
						
					cur.execute(sql, (curr_id, name, name_anc, name_mod, prov, country, pid, gid, name, name_anc, name_mod, prov, country, pid, gid))
					
					conn.commit()

				if (offset + limit >= geo_data["total"]):
					break

				offset += limit

			print(str(num_geo - skipped) + " items handled. " + str(skipped) + " items skipped.")
			
def update_inscriptions (conn, headers, limit):
	api_url = "https://edh-www.adw.uni-heidelberg.de/data/api/inscriptions/search?limit=" + str(limit)
	country_url = "https://edh-www.adw.uni-heidelberg.de/data/api/terms/country"

	with conn.cursor() as cur:

		#Update locations
		# req = urllib.request.Request(country_url, headers=headers)
		# response_data = urllib.request.urlopen(req)
		# countries = json.loads(response_data.read())["countries"]
		countries = {}#TODO!!!!
		
		for country_code in countries:
			if country_code < "tn":
				continue
		
			num = 0
			skipped = 0
			offset = 0
			
			print ("Country " + countries[country_code])
			
			sql = "SELECT edh_id, last_change FROM tools.epigraphik_heidelberg WHERE land = %s"
			cur.execute(sql, (countries[country_code]))
			change_map = {}
			for row in cur.fetchall():
				change_map[row[0]] = row[1].strftime("%Y-%m-%d")
			
			while True:
				url = api_url + "&offset=" + str(offset) + "&country=" + country_code
				print(url)
				req = urllib.request.Request(url, headers=headers)
				
				response = urllib.request.urlopen(req)
				ins_data = json.loads(response.read().decode('utf-8', 'replace'))
				
				print("Got " + str(len(ins_data["items"])) + " items...")
				
				for row in ins_data["items"]:
					curr_id = int(row["id"][2:])
					num += 1

					if curr_id in change_map and change_map[curr_id] > row["last_update"]:
						skipped += 1
						continue
						
					insert_data(curr_id, row, cur, conn, countries[country_code])

				if (offset + limit >= ins_data["total"]):
					break

				offset += limit

			print(str(num - skipped) + " items handled. " + str(skipped) + " items skipped.")
			
		#Update inscriptions without country assignment (new inscriptions without location are ignored for the moment)
		sql = "SELECT edh_id FROM tools.epigraphik_heidelberg WHERE land is null"
		cur.execute(sql)
		
		for row in cur.fetchall():
			url = api_url + "&hd_nr=" + str(row[0])
			
			req = urllib.request.Request(url, headers=headers)
			response = urllib.request.urlopen(req)
			ins_data = json.loads(response.read().decode('utf-8', 'replace'))
			
			if len(ins_data["items"]) == 0:
				sql = "DELETE FROM tools.epigraphik_heidelberg WHERE edh_id = %s"
				cur.execute(sql, (row[0]))
				conn.commit()
			else:
				row = ins_data["items"][0]
				curr_id = int(row["id"][2:])
				insert_data(curr_id, row, cur, conn, None)
			
def insert_data (curr_id, row, cur, conn, country):
	tri_url = "https://www.trismegistos.org/dataservices/texrelations/xml/"

	transcription = None
	if "transcription" in row:
		transcription = row["transcription"]
	
	itype = None
	if "type_of_inscription" in row:
		itype = row["type_of_inscription"]
	
	lang = None
	if "language" in row:
		lang = row["language"]
	
	before = None
	if "not_before" in row:
		before = row["not_before"]
		
	after = None
	if "not_after" in row:
		after = row["not_after"]
		
	loc_id = None
	if "edh_geography_uri" in row:
		loc_uri = row["edh_geography_uri"]
		loc_id = loc_uri[loc_uri.rindex("/") + 1:]
		
	tid = None
	edcs_id = None
	if "trismegistos_uri" in row:
		url = row["trismegistos_uri"]
		
		if not url.startswith("https://www.trismegistos.org/text/"):
			raise Exception("Invalid trismegistos url: " + url)
			
		tid = url[url.rindex("/") + 1:]
		
		req = urllib.request.Request(tri_url + tid, headers=headers)
		response_data = urllib.request.urlopen(req)
		xml = ET.fromstring(response_data.read())
		node = xml.find("link[@cp='EDCS']")
		if node != None:
			edcs_id = node.text
	
	
	fields = (transcription, itype, lang, before, after, tid, edcs_id, loc_id, country, curr_id)
	print(fields)
	
	# sql = """
		# INSERT INTO tools.epigraphik_heidelberg (transkription, typ, sprache, min_jahr, max_jahr, trismegistos_id, edcs_id, id_ort, land, edh_id)
		# VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
		# ON DUPLICATE KEY UPDATE
			# transkription = %s, typ = %s, sprache = %s, min_jahr = %s, max_jahr = %s, trismegistos_id = %s, edcs_id = %s, id_ort = %s, land = %s, last_change = CURRENT_TIMESTAMP
		# """
	# cur.execute(sql, fields + fields[:-1])
		
	
	sql = "SELECT edh_id FROM tools.epigraphik_heidelberg WHERE edh_id = %s"
	cur.execute(sql, (curr_id))
	
	if cur.fetchone():
		print("update")
		sql = "UPDATE tools.epigraphik_heidelberg SET transkription = %s, typ = %s, sprache = %s, min_jahr = %s, max_jahr = %s, trismegistos_id = %s, edcs_id = %s, id_ort = %s, land = %s, last_change = CURRENT_TIMESTAMP WHERE edh_id = %s"
		cur.execute(sql, fields)
	else:
		print ("new")
		sql = "INSERT INTO tools.epigraphik_heidelberg (transkription, typ, sprache, min_jahr, max_jahr, trismegistos_id, edcs_id, id_ort, land, edh_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
		cur.execute(sql, fields)
		
	conn.commit()
			

if __name__ == "__main__":

	limit = 500
	headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0"}

	# sparql_geo_ids = """
		# PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
		
		# SELECT DISTINCT ?geo_id
		# WHERE { 
			# ?s ?p ?o.
			# FILTER regex(str(?s), "http://edh-www.adw.uni-heidelberg.de/edh/geographie/", "i").
			# BIND (xsd:int(strafter(str(?s), "http://edh-www.adw.uni-heidelberg.de/edh/geographie/")) as ?geo_id)
			# FILTER (?geo_id > -1)
		# } 
		# ORDER BY ASC(?geo_id)
		# LIMIT 50
		# """
	#query_url = "https://edh-www.adw.uni-heidelberg.de/data/query?output=json&query="

	conn = conn_3312("tools")

	try:
		#update_locations(conn, headers, limit)
		update_inscriptions(conn, headers, limit)
	finally:
		conn.close()
	
	
	