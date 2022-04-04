import os
import re

import sys
sys.path.append(sys.path[0] + "/../lib")
from util import conn_3312, get_login_data

#Import dump with:
# dbdump>mysql -P 3311 -u root va_xxx < va_dump.sql

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("Usage python local_db <folder_for_dump>")
		exit()

	folder = sys.argv[1] + "/"

	with conn_3312().cursor() as cur:
		sql = "SHOW FULL TABLES IN va_xxx WHERE TABLE_TYPE = 'BASE TABLE'"
		cur.execute(sql)
		tables = map(lambda x: x[0], cur.fetchall())
		
		sql = "SHOW FULL TABLES IN va_xxx WHERE TABLE_TYPE = 'VIEW'"
		cur.execute(sql)
		views = map(lambda x: x[0], cur.fetchall())
		
		sql = "SHOW PROCEDURE STATUS WHERE Db = 'va_xxx'"
		cur.execute(sql)
		procedures = map(lambda x: x[1], cur.fetchall())
		
		sql = "SHOW FUNCTION STATUS WHERE Db = 'va_xxx'"
		cur.execute(sql)
		functions = map(lambda x: x[1], cur.fetchall())

	ldata = get_login_data()
	usr = ldata[0]
	pwd = ldata[1]
		
	#TABLES
	cmd = "mysqldump -P 3312 -u " + usr + " -p" + pwd + " --disable-keys --skip-triggers --default-character-set=utf8mb4 --result-file=" + folder + "va_dump.sql va_xxx " + " ".join(tables)
	print(cmd)
	os.system(cmd)
	
	#PROCEDURES / FUNCTIONS
	sources = []
	with conn_3312().cursor() as cur:
		for fun in functions:
			sql = "SHOW CREATE FUNCTION " + fun
			cur.execute(sql)
			source = cur.fetchone()[2]
			if not source:
				continue
			sources.append(re.sub(" DEFINER=[^ ]*", "", source))
			
		for proc in procedures:
			sql = "SHOW CREATE PROCEDURE " + proc
			cur.execute(sql)
			source = cur.fetchone()[2]
			if not source:
				continue
			sources.append(re.sub(" DEFINER=[^ ]*", "", source))
			
	with open(folder + "va_dump.sql", "a") as procFile:
		print ("DELIMITER $$", file=procFile)
		for source in sources:
			print(source + ";", file=procFile)
	
	#VIEWS
	cmd = "mysqldump -P 3312 -u " + usr + " -p" + pwd + " --disable-keys --default-character-set=utf8mb4 --result-file=" + folder + "dump_temp.sql va_xxx " + " ".join(views)
	print(cmd)
	os.system(cmd)
	
	with open(folder + "dump_temp.sql", "r") as temp_file:
		with open(folder + "va_dump.sql", "a", encoding="utf8") as dump_file:
			for line in temp_file.readlines():
				if not line.startswith("/*!50013"):
					print(line, file=dump_file, end="")
				
	os.remove(folder + "dump_temp.sql")
				
	