import pymysql
import json
import sys
sys.path.append(sys.path[0] + "/../lib")
from util import conn_3312

if __name__ == "__main__":

	conn = conn = conn_3312()

	with conn.cursor() as cur, open("eth_pois.json", encoding="utf8") as f:
		data = json.load(f)
		
		loc_mapping = {}
		
		c = 0
		for row in data["data"]["pois"]:
			sql = "SELECT Id_Ort, Name FROM Orte WHERE Id_Kategorie = 62 AND QID = %s"
			cur.execute(sql, row["qid"][1:])
			vadata = list(cur.fetchall())
			
			if  len(vadata) > 0:
				c+=1
			
			if len(vadata) > 1:
				print("Multiple rows: " + str(row) + "\n" + str(vadata))
			elif len(vadata) == 1:
				if vadata[0][0] not in loc_mapping:
					loc_mapping[vadata[0][0]] = {"name": vadata[0][1], "rows": []}
				loc_mapping[vadata[0][0]]["rows"].append(row)
				
		print(c)
				
		for id_loc, info in loc_mapping.items():
			if len(info["rows"]) > 1:
				use = False
				for row in info["rows"]:
					if row["name_de"].strip() == info["name"].strip():
						use = row
						break
						
				if use == False:
					#Take first element if there are multiple
					use = info["rows"][0]
					
				sql = "UPDATE Orte SET ETH_ID = %s WHERE Id_Ort = %s"
				cur.execute(sql, (use["id"], id_loc))
					
				# if use == False:
					# print("No name match found for VA-Name: " + info["name"] + ", ETH-Names: " + ", ".join(map(lambda x: x["name_de"], info["rows"])))
		conn.commit();

			
		

		
		