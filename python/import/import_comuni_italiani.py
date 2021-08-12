import urllib.request
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
import sys
sys.path.append(sys.path[0] + "/../lib")
from util import conn_3312

class LinkFinder(HTMLParser):
	def __init__ (self, regex):
		self.regex = regex
		self.links = []
		super(LinkFinder, self).__init__()

	def handle_starttag(self, tag, attrs):
		for attr in attrs:
			if attr[0] == "href" and re.match(self.regex, attr[1]):
				self.links.append(attr[1])
				break

	def handle_endtag(self, tag):
		pass

	def handle_data(self, data):
		pass
		
	def get_links (self):
		return self.links
		
class StatParser(HTMLParser):

	def __init__ (self):
		self.row_data = []
		self.rows = []
		self.in_h1 = False
		self.in_stat = False
		self.in_td = False
		
		super(StatParser, self).__init__()

	def handle_starttag(self, tag, attrs):
		if tag == "h1":
			self.in_h1 = True
		if tag == "table":
			for attr in attrs:
				if attr[0] == "class" and attr[1] == "tabwrap":
					self.in_stat = True
		if tag == "tr" and self.in_stat:
			self.row_data = []
		if tag == "td" and self.in_stat:
			self.in_td = True


	def handle_endtag(self, tag):
		if tag == "h1":
			self.in_h1 = False
		if tag == "table":
			self.in_stat = False
		if tag == "tr" and self.in_stat:
			if len(self.row_data) > 0:
				self.rows.append(self.row_data)
		if tag == "td" and self.in_stat:
			self.in_td = False
		
	def handle_data(self, data):
		if self.in_h1:
			self.name = data.replace("Popolazione ", "").replace(" 1861-2016", "")
		if self.in_td:
			self.row_data.append(data)
			
	def get_data (self):
		if self.rows:
			if self.rows[0][1] != "Anno" and self.rows[0][3] != "Residenti":
				raise Exception("Table not valid")
				
			return {
				"name": self.name, 
				"hist": [{
					"year": int(r[0].replace(" ind", "")), 
					"population": int(r[1].replace(".",""))
				} for r in self.rows[1:]]
			}
		else:
			return None


if __name__ == "__main__":
	max_list_num = 98 #number of groups on the community overview page http://www.comuni-italiani.it/alfa/index.html
	conn = conn_3312()
	sql = "INSERT INTO tools.comuni_italiani_popolazione VALUES (%(prov_id)s, %(com_id)s, %(name)s, %(year)s, %(population)s)"
	
	for i in range(1, max_list_num + 1):
		coms = []
		link = "http://www.comuni-italiani.it/alfa/" + str(i).zfill(3) + ".html"
		path = urllib.request.urlopen(link)
		content = path.read().decode("utf-8", errors="ignore")
		parser = LinkFinder("^\.\./[0-9]{3}/[0-9]{3}/index.html$")
		parser.feed(content)
		for l in parser.get_links():
			coms.append({"prov_id": l[3:6], "com_id" : l[7:10], "link": "http://www.comuni-italiani.it" + l.replace("..", "").replace("/index.html", "") + "/statistiche/popolazione.html"})
		
		data = []
		for com in coms:
			print(com["link"])
			s = StatParser()
			path = urllib.request.urlopen(com["link"])
			content = path.read().decode("utf-8", errors="ignore")
			s.feed(content)
			cdata = s.get_data()
			if cdata:
				for row in cdata["hist"]:
					data.append(com | {"name": cdata["name"], "year" : row["year"], "population": row["population"]})
			else:
				print("Skipped")

		with conn.cursor() as cur:
			cur.executemany(sql, data)
		
		conn.commit()
		