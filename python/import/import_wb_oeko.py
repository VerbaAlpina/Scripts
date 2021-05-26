from xml.dom import minidom

#gswin64c -sDEVICE=txtwrite -dTextFormat=0 -o output2.txt 2012_book_woerterbuchderoekologie.pdf + regex "<char bbox="[^"]*" c="([^"]*)"/>\n" -> \1

if __name__ == "__main__":
	file = "C:/Users/fz/Desktop/output2_w.txt"

	with open("wb_oeko.txt", "w", encoding = "utf-8-sig") as ofile:

		xmldoc = minidom.parse(file)
		last_y = None
		cline = ""
		for span in xmldoc.getElementsByTagName('span'):
			if span.attributes["font"].value == "WNANXQ+Arial-BoldMT":
				string = span.firstChild.nodeValue.strip()
				if len(string) > 0:
					cur_y = span.attributes["bbox"].value.split()[1]
					if last_y != cur_y:
						print(cline, file=ofile)
						last_y = cur_y
						cline = ""
					cline += (" " if cline != "" else "") + string
					
		