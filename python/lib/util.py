import pymysql
import socket
import os

#A file "login" with the following structure is needed:
# first line: 3312 user
# second line: 3312 password
# third line: 3306 user
# fourth line: 3306 password
# fifth line: hostname for localhost

def get_login_data ():
	with open(os.path.dirname(os.path.realpath(__file__)) + "/login") as file:
		data = map(lambda x: x[:-1] if x[-1] == "\n" else x, file.readlines())
		return list(data)

def conn_3312 (db = "va_xxx"):

	ldata = get_login_data()
	if socket.gethostname() == ldata[4]:
		host = "localhost"
	else:
		host = "gwi-sql"
	
	return pymysql.connect(host= host, port=3312, db=db, user=ldata[0], passwd=ldata[1], charset='utf8')
	
def conn_3306 (db = "kit"):

	ldata = get_login_data()
	if socket.gethostname == ldata[4]:
		host = "localhost"
	else:
		host = "gwi-sql"
	
	return pymysql.connect(host= host, port=3306, db=db, user=ldata[2], passwd=ldata[3], charset='utf8')
	
def va_procedure_url (ptype, pname):
	return "https://raw.githubusercontent.com/VerbaAlpina/SQL/master/procedures/" + ptype + "/" + pname + ".sql"