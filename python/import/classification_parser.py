import os
import re
import csv
import pandas
import json
import matplotlib.pyplot as plt
import matplotlib

from datetime import date
import sys
sys.path.append(sys.path[0] + "/../lib")
from util import conn_3312

from PIL import Image

def parse_zooniverse_csv():
	"""
	Reads the Zooniverse Data Export and parsed the Classifications in a wellformed CSV File
	"""
	
	workflows = [11976, 18234]
	
	parsed_data = []
	df = pandas.read_csv("verbaalpina-classifications.csv")
	annotations = df["annotations"]
	subject_data = df["subject_data"]
	
	for index, row in df.iterrows():
		if not row["workflow_id"] in workflows:
			continue
	
		annotation = json.loads( row['annotations'])[0]
		subject_data = json.loads(row['subject_data'])
		values = annotation["value"]

		author = row['user_name']
		user_id = str(row['user_id'])
		created_at = row['created_at']
		classification_id = row['classification_id']
		workflow_id = row['workflow_id']

		subject_key, subject_value =  next(iter( subject_data.items() ))

		if "current_subject_number" in subject_value:
			image_name = "subject_data/" + subject_value["current_subject_number"]

			name = subject_value["current_subject_number"].replace(".jpg", "")
			file_name = "current_results/" +  name + "-(current markings)" + ".png"

			for key, value in enumerate(values):
				current_x = value["x"]
				current_y = value["y"]
				current_width = value["width"]
				current_height = value["height"]

				detail_number = value["details"][0]["value"]
				detail_transcription = value["details"][1]["value"]

				if True: #detail_number != "":

					map_id = subject_value["current_subject_number"].split("#")[1]
					map_id = map_id.split("-")[0]

					parsed_data.append({
						"classification_id" : classification_id,
						"workflow" : workflow_id,
						"user": author,
						"user_id": user_id,
						"created_at": created_at,
						"subject_id": subject_value["current_subject_number"],
						"num_box": str(key),
						"map_id":map_id,
						"map_number":detail_number,
						"transcription": detail_transcription.strip(),
						"x":current_x,
						"y":current_y,
						"width":current_width,
						"height":current_height
						})
						

	conn = conn_3312("va_temp")
	with conn.cursor() as cur:
		today = date.today()
		table_name = "zooniverse_" + today.strftime("%Y_%m_%d")
			
		sql = "CREATE TABLE `" + table_name + "` (num INT UNSIGNED PRIMARY KEY, classification_id INT UNSIGNED, workflow INT UNSIGNED, `user` VARCHAR(100), user_id VARCHAR(100), created_at TIMESTAMP, subject_id VARCHAR(100), num_box INT UNSIGNED, map_id INT UNSIGNED, map_number INT UNSIGNED, transcription VARCHAR(1000), x INT UNSIGNED, y INT UNSIGNED, width INT unsigned, height INT unsigned)"
		cur.execute(sql)
		
		crows = []
		sql = "INSERT INTO `" + table_name + "` VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
		
		for i, row in enumerate(parsed_data):
			crows.append([i] + list(row.values()))
		
			if len(crows) == 10000:
				cur.executemany(sql, crows)
				crows = []
				print(i, "/", len(parsed_data))
				
		if crows:
			cur.executemany(sql, crows)
			
		
		conn.commit()

	#data_frame = pandas.DataFrame(parsed_data)
	#data_frame.to_csv("verbaalpina-zooniverse-transcription.csv", sep="§")


def crop_annotations():
	"""
	Reads the well parsed CSV, and the images from the subject set (need to be added in the main folder as "subject data")
	outputs JPG Images of the markings done in the classinfications
	"""
	df = pandas.read_csv("verbaalpina-classifications.csv")
	annotations = df["annotations"]
	subject_data = df["subject_data"]

	for index, row in df.iterrows():
		annotation = json.loads( row['annotations'])[0]
		subject_data = json.loads(row['subject_data'])
		values = annotation["value"]

		author = row['user_name']
		user_id = row['user_id']
		created_at = row['created_at']
		classification_id = row['classification_id']

		subject_key, subject_value =  next(iter( subject_data.items() ))

		if "current_subject_number" in subject_value:
			image_name = "subject_data/" + subject_value["current_subject_number"]

			name = subject_value["current_subject_number"].replace(".jpg", "")
			file_name = "current_results/" +  name + "-(current markings)" + ".png"

			# pillow
			im = Image.open(image_name)
			im_width, im_height = im.size

			# ploting
			img = matplotlib.image.imread(image_name)
			figure, ax = plt.subplots(1)
			ax.imshow(img)

			for key, value in enumerate(values):
				current_x = value["x"]
				current_y = value["y"]
				current_width = value["width"]
				current_height = value["height"]

				detail_number = value["details"][0]["value"]
				detail_transcription = value["details"][1]["value"]

				# plot visualisation
				rect = matplotlib.patches.Rectangle((current_x,current_y),current_width,current_height, edgecolor='r', facecolor="none")
				ax.add_patch(rect)

				# pillow cropping
				(left, upper, right, lower) =  ( current_x, current_y, current_x + current_width , current_y + current_height )
				im_crop = im.crop(box=(left, upper, right, lower))
				file_name = "current_results/" +  name + "-" + str(key)+ ".png"
				im_crop.save(file_name, quality=95)

			figure.show()

			# save plot
			name = subject_value["current_subject_number"].replace(".jpg", "")
			plt.savefig(file_name)


if __name__ == "__main__":
	parse_zooniverse_csv()
