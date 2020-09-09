import pymysql
import socket

#A file with the following structure is needed:
# first line: 3312 user
# second line: 3312 password
# third line: 3306 user
# fourth line: 3306 password
# fifth line: hostname for localhost

def get_login_data ():
	with open("login"):
		data = readlines()
		print (data)

def conn_3312 (version = "va_xxx"):
	if socket.gethostname() in localhosts:
		host = "localhost"
	else:
		host = "gwi-sql"
	
	return pymysql.connect(host= host, port=3312, db=version, user=user, passwd=passw, charset='utf8')
	
def user_3312 ():
	return user
	
def password_3312 ():
	return passw
	
def conn_3306 (db = "kit"):
	if socket.gethostname() in localhosts:
		host = "localhost"
	else:
		host = "gwi-sql"
	
	return pymysql.connect(host= host, port=3306, db=db, user=kit_user, passwd=passw, charset='utf8')