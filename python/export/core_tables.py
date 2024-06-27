import sys
import os
import getpass

sys.path.append(sys.path[0] + "/../lib")
from util import conn_3312

if __name__ == "__main__":
	conn = conn_3312("va_xxx")
	
	with conn.cursor() as cur:
		sql = "SELECT name FROM doku_tabellen WHERE kategorie = 'Projektdaten'"
		cur.execute(sql)
		tables = list(map(lambda x: x[0], cur.fetchall()))
		
		sql = "SELECT Nummer FROM versionen WHERE Website"
		cur.execute(sql)
		
		print ("== Data base connection === ")
		user = input("Nutzername: ")
		pw = getpass.getpass()
		
		for (vnum,) in cur.fetchall():
			print("Handle " + vnum + "...")
			cmd = "mysqldump -h gwi-sql.gwi.uni-muenchen.de -P 3312 -u " + user + " -p" + pw + " --ssl --disable-keys --skip-triggers --default-character-set=utf8mb4 --result-file=projektdaten_" + vnum + ".sql va_" + vnum + " " + " ".join(tables)
	
			os.system(cmd)