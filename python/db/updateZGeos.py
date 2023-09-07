import pymysql
import getpass
import requests

import sys
sys.path.append(sys.path[0] + "/../lib")
from util import conn_3312

if __name__ == "__main__":
	url = "https://raw.githubusercontent.com/VerbaAlpina/SQL/master/procedures/z_tables/zgeo.sql"
	r = requests.get(url, allow_redirects=True)

	lines = r.text.split('\n')
	zsql = "\n".join(lines[1:-1]).split("$$")
	
	conn = conn_3312()
	
	with conn.cursor() as cur:
		sql = "SELECT Nummer FROM va_xxx.Versionen WHERE Website UNION SELECT 'xxx'"
		cur.execute(sql)
		versions = cur.fetchall()
		
	conn.close();
	
	for version in versions:
		conn = conn_3312("va_" + version[0])
		conn.autocommit(True)
		
		with conn.cursor() as cur:
			print ("Updating va_" + version[0])
			
			for zs in zsql:
				if not zs.isspace():
					cur.execute(zs)
				
			sql = "CALL zgeo()"
			cur.execute(sql)
			
		conn.close()