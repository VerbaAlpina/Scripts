import pymysql
import getpass
import sys
import re
import os
from subprocess import run


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print ("No data base name given!")
		sys.exit()
		
	newDB = sys.argv[1]

	print ("== Data base connection === ")
	user = input("Nutzername: ")
	pw = getpass.getpass()

	os.system("mysqldump --routines -h gwi-sql.gwi.uni-muenchen.de -P 3312 -u " + user + " -p" + pw + " --ssl va_xxx > D:/backup/dump.sql")
	
	conn = pymysql.connect(host= "gwi-sql.gwi.uni-muenchen.de", port=3312, db="va_xxx", user=user, passwd=pw, charset='utf8', ssl=True)
	with conn.cursor() as cur:
		sql = "SELECT COUNT(*) FROM `information_schema`.`columns` WHERE `table_schema` = '" + newDB + "'"
		cur.execute(sql)
		count = cur.fetchone()
		
		if int(count[0]) > 0:
			print ("Database is not empty!")
			sys.exit()
		
		os.system("mysql -h localhost -P 3312 -u " + user + " -p" + pw + " " + newDB + " < D:/backup/dump.sql")
	