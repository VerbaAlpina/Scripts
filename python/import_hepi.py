import urllib.request
import urllib.parse
import json
import sys
sys.path.append(sys.path[0] + "/lib")
from util import get_login_data

if __name__ == "__main__":

	get_login_data()
	exit()

	query_url = "https://edh-www.adw.uni-heidelberg.de/data/query?output=json&query="
	geo_url = "https://edh-www.adw.uni-heidelberg.de/edh/geographie/"

	curr_id = -1
	
	headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0"}
	
	sql = "UPDATE tools.epigraphik_heidelberg_orte SET updated = 0"
	
	while True:
		sparql_geo_ids = """
		PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
		
		SELECT DISTINCT ?geo_id
		WHERE { 
			?s ?p ?o.
			FILTER regex(str(?s), "http://edh-www.adw.uni-heidelberg.de/edh/geographie/", "i").
			BIND (xsd:int(strafter(str(?s), "http://edh-www.adw.uni-heidelberg.de/edh/geographie/")) as ?geo_id)
			FILTER (?geo_id > """ + str(curr_id) + """)
		} 
		ORDER BY ASC(?geo_id)
		LIMIT 1000
		"""
		
		url = query_url + urllib.parse.quote_plus(sparql_geo_ids)
		req = urllib.request.Request(url, headers=headers)
		
		response = urllib.request.urlopen(req)
		id_list = json.loads(response.read())
		for row in id_list["results"]["bindings"]:
			curr_id = int(row["geo_id"]["value"])
			data_url = geo_url + str(curr_id) + "&format=json"
			req = urllib.request.Request(data_url, headers=headers)
			
			response_data = urllib.request.urlopen(req)
			data = json.loads(response_data.read())["features"][0]
			
			lat = data["geometry"]["coordinates"][0]
			lng = data["geometry"]["coordinates"][1]
					
			geo_string = "POINT(" + str(lat) + " "  + str(lng) + ")"
			
			sql = """
				INSERT INTO tools.epigraphik_heidelberg_orte (name, province, country, pleiades_id, trismegistos_id, geo_data)
				VALUES (%s, %s, %s, %s, %s, GeomFromText('""" + geo_string + """'))
				ON DUPLICATE KEY UPDATE
					name = %s, province = %s, country = %s, pleiades_id = %s, trismegistos_id = %s, geo_data = GeomFromText('""" + geo_string + """')
				"""
				
			print(sql)
			break
		
		break
		
		