##########################
###     MODEL CLASS    ###
##########################

from .sqlite_manager import SqliteManager
from .pdf_manager import PDFManager
from .record_types import PDFRecord, CSVRecord
from .schema_translator import SchemaTranslator
import csv
import pandas as pd
from PyPDF2 import PdfWriter, PdfReader
import re
from datetime import datetime
import os


class Model:
	def __init__(self, config):
		self._files = [None, None]
		self._db = None
		self._db_schema = SchemaTranslator(config['database']['schema_path'])
		self._patterns = None
		# Attributes for the csv data scan
		self._data_patterns = None
		self._max_scan_rows = 100
		# Attributes for the shipment data
		self._shipment_details = None
		self._shipment_data = None
		self._shipment_labels = None
		if not self._db:
			self.initialize_db(config['database'])
		if not self._patterns:
			self.initialize_patterns()


	# Set up the database
	def initialize_db(self, database):
		self._db = SqliteManager(database['path'], self._db_schema)
		self._db.connect()
		self._db.setup_tables()
		self._db.close()

	# Initialize the PDF Manager
	pdf_mgr = PDFManager('files/pdfs/')

	# Set up the data patterns
	def initialize_patterns(self):
		self._patterns = {
			'shipment_details': {
				'rows': 1,
				'cols': 2,
				'orientation': 'rows',
				'fixed': 'cols',
				'data_labels': ['shipment id', 'shipment name', 'boxes', 'units']
			},
			'shipment_data': {
				'rows': 2,
				'cols': 3,
				'orientation': 'cols',
				'fixed': None,
				'data_labels': ['sku', 'total boxes', 'total units', 'box id']
			} 
		}

	##############  SETTERS  ##################
	def set_csv_record(self, file_path):
		# Check if the record already exists
		if not self.get_csv_record():
			record = CSVRecord()
			if record:
				record.set_path(file_path)
				self._files[0] = record
		# If record exists just update the path
		else:
			record = self.get_csv_record()
			record.set_path(file_path)

		return record

	def set_pdf_record(self, file_path):
		if not self.get_pdf_record():
			record = PDFRecord()
			if record:
				record.set_path(file_path)
				self._files[1] = record
		else:
			record = self.get_pdf_record()
			record.set_path(file_path)
		
		return record

	def set_data_patterns(self, data_array):
		self._data_patterns = data_array

	def set_shipment_details(self, shipment_details_dict):
		self._shipment_details = shipment_details_dict

	def set_shipment_data(self, shipment_data_dataframe):
		self._shipment_data = shipment_data_dataframe


  ##############  GETTERS  ##################
	def get_csv_record(self):
		return self._files[0]

	def get_pdf_record(self):
		return self._files[1]

	def get_data_patterns(self):
		return self._data_patterns

	def get_one_pattern(self, name):
		return self._patterns[name]

	def get_shipment_details(self):
		return self._shipment_details

	def get_shipment_data(self):
		return self._shipment_data

	##############  UTILITY METHODS  ################

	# Utility function to trim rows normalized with trailing commas
	def trim_trailing_empty_cells(self, row):
		while row and row[-1] == '':
			row.pop()
		return row 

	# Utility function to find the first blank row (max 20 rows scanned)
	def csv_search_blank_row(self, file_path):

		with open(file_path, 'r', encoding='utf-8-sig', newline='') as file:

			reader = csv.reader(file)
			for index, row in enumerate(reader):
				if index > 20:
					break
				elif all(not cell.strip() for cell in row):
					return index
		
		return None

	# Utility function to return the row length if uniform or None if not
	def csv_find_row_lengths(self, file_path, end_index, start_index=0):

		with open(file_path, 'r', encoding='utf-8-sig', newline='') as file:

			reader = csv.reader(file)
			row_lengths = set()
			for index, row in enumerate(reader):
				if index < start_index:
					pass
				elif index < end_index:
					row_length = len(row)
					print(row_length)
					row_lengths.add(row_length)
				elif index >= end_index:
					break
			
			if len(row_lengths) == 1:
				return row_lengths.pop()
			else:
				return None

	# Utility function to check data segment for empty leading columns
	# Returns num cols if uniform leading blank cols, 0 if no blanks, and -1
	# if blank cols are not uniform
	def find_leading_cols(self, file_path, end_index, start_index=0):

		with open(file_path, 'r', encoding='utf-8-sig', newline='') as file:

			reader = csv.reader(file)
			leading_blank = set()

			for index, row in enumerate(reader):
				if index < start_index:
					pass

				elif index < end_index:
					count = 0
					for i, cell in enumerate(row):
						if cell.strip() == '':
							count = i + 1
						else:
							break
					if count > 0:
						leading_blank.add(count)

				elif index >= end_index:
					break
			
			if len(leading_blank) > 1:
				return -1
			elif len(leading_blank) == 1:
				return leading_blank.pop()
			else:
				return 0
		

	def csv_search_shipment_details(self, file, end_index):
		pass


	# Takes a CSV file path. Returns array of recognized data patterns
	def find_data_patterns(self, file_path):

		with open(file_path, 'r', encoding='utf-8-sig', newline='') as file:

			reader = csv.reader(file)
			curr_cols = None
			leading_trailing = False
			data_segments = None
			for index, row in enumerate(reader):

				# Trim row of any trailing commas
				row = self.trim_trailing_empty_cells(row)

				# First scan, initialize variables
				if not data_segments and not curr_cols and index == 0:
					data_segments = []
					start_index = 0
					num_rows = 0
					num_cols = len(row)
					# Check if this first row has no data in it
					if num_cols == 0:
						leading_trailing = True
					active_segment = True

				curr_cols = len(row)

				# Recognized a new pattern, create new segment and add to array
				if curr_cols != num_cols:
					data_segment = {
						'indices': (start_index, index),
						'size': (num_rows, num_cols),
						'ignore_leading_trailing': leading_trailing
					}
					data_segments.append(data_segment)
					leading_trailing = False

					# Adjust indices for new pattern
					start_index = index
					num_rows = 1
					num_cols = curr_cols

				# Reached max scan limit, create new segment, add to array and break loop
				elif index > self._max_scan_rows:
					data_segment = {
						'indices': (start_index, index),
						'size': (num_rows, num_cols),
						'ignore_leading_trailing': leading_trailing
					}
					data_segments.append(data_segment)
					leading_trailing = False
					active_segment = False
					break

				# Pattern is the same as prior row, continue scanning
				elif curr_cols == num_cols:
					num_rows += 1

			# Load last data pattern in after loop break if active segment is found
			index += 1 # end_index is not inclusive even if end of file
			if active_segment:
				if num_cols == 0:
					leading_trailing = True
				data_segment = {
						'indices': (start_index, index),
						'size': (num_rows, num_cols),
						'ignore_leading_trailing': leading_trailing
					}
				data_segments.append(data_segment)

			return data_segments

	# Takes an array of data patterns, and a pattern, and returns the date
	# that matches, if any. Returns None if no match
	def find_pattern_match(self, to_match, data_patterns):

		size = {
			'rows': 0,
			'cols': 1
		}
		matches = []
		fixed_dim = to_match['fixed']

		# 'shipment_data': {
		# 	'rows': 2,
		# 	'cols': 3,
		# 	'orientation': 'cols',
		# 	'fixed': None,
		# 	'data_labels': ['sku', 'total boxes', 'total units', 'box id']
		# }

		for index, pattern in enumerate(data_patterns):
			if fixed_dim:
				if pattern['size'][size[fixed_dim]] == to_match[fixed_dim]:
					matches.append(pattern)
			else:
				rows = pattern['size'][0]
				cols = pattern['size'][1]
				# DELETE Test print
				# print(f"Pattern rows: {rows}, cols: {cols}")
				if (rows >= to_match['rows']) and (cols >= to_match['cols']):
					matches.append(pattern)
		
		# Right now this only returns the first match
		return matches[0]


	# Takes an array of data pattern dictionary objects and prints for viewing
	def print_data_patterns(self, data_patterns):
		for index, pattern in enumerate(data_patterns):
			print(f"Pattern {index + 1}")
			print(f"Indices at: {data_patterns[index]['indices']}")
			print(f"Rows: {data_patterns[index]['size'][0]}, Columns: {data_patterns[index]['size'][1]}")
			print(f"Ignore flag: {data_patterns[index]['ignore_leading_trailing']}")
			print(f"------------------------------")


	def validate_shipment_details(self, data, data_pattern):
		
		data_labels_array = data_pattern['data_labels']

		# Initialize data_labels match to False
		validate = False

		# Loop through all the data_labels
		for data_label in data_labels_array:
			match = False
			# Loop through the keys to see if there is a match
			for key in data:
				if key.lower() == data_label.lower():
					match = True
					break
			# If only one false match the data doesn't validate
			if match == False:
				break
		# If the last match is true the data must validate
		if match == True:
			validate = True
		
		return validate

	def validate_shipment_data(self, file_path, data_pattern, pattern_match):

		# 'shipment_data': {
		# 	'rows': 2,
		# 	'cols': 3,
		# 	'orientation': 'cols',
		# 	'fixed': None,
		# 	'data_labels': ['sku', 'total boxes', 'total units', 'box id']
		# }

		data_labels_array = data_pattern['data_labels']
		# This can be used in the future for flexible validation of data by
		# rows or by columns
		# orientation = data_pattern['orientation']

		# Initialize data_labels match to False
		validate = False
		data_header_row = []

		start_index = pattern_match['indices'][0]

		with open(file_path, 'r', encoding='utf-8-sig', newline='') as file:

			reader = csv.reader(file)
			for index, row in enumerate(reader):
				
				# Trim row of any trailing commas
				row = self.trim_trailing_empty_cells(row)
				if index == start_index:
					for cell in row:
						data_header_row.append(cell.strip())
					break
				else:
					pass

		# Loop through all the data_labels
		for data_label in data_labels_array:
			match = False
			# Loop through the keys to see if there is a match
			for key in data_header_row:
				if key.lower() == data_label.lower():
					match = True
					break
			# If only one false match the data doesn't validate
			if match == False:
				break
		# If the last match is true the data must validate
		if match == True:
			validate = True
		
		return validate


	def read_shipment_details(self, file_path, data_pattern):

		with open(file_path, 'r', encoding='utf-8-sig', newline='') as file:

			# EXAMPLE
			# data_pattern = {
			# 	'indices': (start_index, index),
			# 	'size': (num_rows, num_cols),
			# 	'ignore_leading_trailing': leading_trailing
			# }

			start_index = data_pattern['indices'][0]
			end_index = data_pattern['indices'][1]
			num_cols = data_pattern['size'][1]
			shipment_details = {}

			reader = csv.reader(file)
			for index, row in enumerate(reader):
				
				# Trim row of any trailing commas
				row = self.trim_trailing_empty_cells(row)

				if index < start_index:
					pass
				elif index < end_index:
					if len(row) == num_cols:
						key = row[0].strip()
						value = row[1].strip()
						shipment_details[key] = value
					else:
						break
				elif index >= end_index:
					break

		return shipment_details
				



	##############  MODEL METHODS  ##################
	def verify_data_match(self):

		shipment_data = self.get_shipment_data()
		shipment_labels_path = self.get_pdf_record().get_path()

		with open(shipment_labels_path, 'rb') as file:
			shipment_labels = PdfReader(file)

			# Box quantity verification check
			# Shipment details from the model
			shipment_details_data = self.get_shipment_details()
			if int(shipment_details_data['Boxes']) != int(len(shipment_labels.pages) / 2):
			# if int(shipment_details['Boxes']) != int(len(shipment_labels.pages) / 2):
				print("Box counts do not match")
			else:
				print("Box counts match")

			# Sort shipment data by box ID
			sorted_data = shipment_data.sort_values(by='Box ID')

			# Set index for the pdf labels file
			pdf_page_index = 0

			for _, row in sorted_data.iterrows():
				box_id = row['Box ID']
				sku = row['SKU']

				# Extract the text from the pdf
				text_page = shipment_labels.pages[pdf_page_index].extract_text()

				# Increment the index by 2 to skip over the shipping label
				pdf_page_index += 2

				if str(box_id) not in text_page or sku not in text_page:
					print(f"Mismatch found for Box ID {box_id} and SKU {sku}")
					return False

			# All checks pass 
			return True


	def split_shipment_labels(self):

		shipment_data = self.get_shipment_data()
		shipment_labels_path = self.get_pdf_record().get_path()

		with open(shipment_labels_path, 'rb') as file:
			shipment_labels = PdfReader(file)

			# Sort shipment data by box ID
			sorted_data = shipment_data.sort_values(by='Box ID')

			# A dictionary to store the sku(key) and a page range tuple
			sku_pages = {}

			# Set page index for pdf labels file
			page_start_index = 0
			page_end_index = 0

			# Set current sku
			current_sku = None

			for _, row in sorted_data.iterrows():
				sku = row['SKU'].strip()

				if not current_sku:
					# Just started reading
					current_sku = sku

				elif current_sku and (current_sku != sku):
					# New sku set reached, store the data in the sku pages dict
					sku_pages[current_sku] = (page_start_index, page_end_index)
					page_start_index = page_end_index
					current_sku = sku

				page_end_index += 2

			# Final record as the loop breaks
			sku_pages[current_sku] = (page_start_index, page_end_index)

		############### REFACTOR TO A MERGE PAGES METHOD ##########
		# Right now this only works to set active labels. Would be way more
		# flexible if it were in a method that could be used for both active
		# and archived labels
		for pages_set in sku_pages:
			self.pdf_mgr.process_pdf_pages(
				shipment_labels_path,
				pages_set, True, sku_pages[pages_set])	

	

	def write_csv_to_main(self):

		shipment_data = self.get_shipment_data()

		# Output to the main record file
		main_file_loc = 'files/main.csv'

		if os.path.exists(main_file_loc) and os.path.getsize(main_file_loc) > 0:
			try:
				existing_data = pd.read_csv(main_file_loc)
				updated_data = pd.concat([existing_data, shipment_data])
				sorted_data = updated_data.sort_values(by=['SKU', 'Date', 'Shipment ID'])
				sorted_data.to_csv(main_file_loc, index=False)
			except pd.errors.EmptyDataError:
				sorted_data = shipment_data.sort_values(by=['SKU', 'Date', 'Shipment ID'])
				sorted_data.to_csv(main_file_loc, index=False)
		else:
			sorted_data = shipment_data.sort_values(by=['SKU', 'Date', 'Shipment ID'])
			sorted_data.to_csv(main_file_loc, index=False)


	# Heavy lifting method that reads in the csv file, matches patterns to
	# locate the data, creates the dataframe (future: split off) and stores in
	# the model
	def read_csv(self):

		file_path = self.get_csv_record().get_path()

		# Identify the data patterns in the csv file and store them
		patterns = self.find_data_patterns(file_path)
		self.set_data_patterns(patterns)

		# Look for a match
		# This result matches the shipment details data
		pattern_match = self.find_pattern_match(self.get_one_pattern('shipment_details'), self.get_data_patterns())

		# Pull the data according to the matched pattern
		# Returns a dictionary
		data_details = self.read_shipment_details(file_path, pattern_match)

		# Validate the data matches expected key details
		validate_check = self.validate_shipment_details(data_details, self.get_one_pattern('shipment_details'))

		# If validation passes store the shipment details
		if validate_check:
			self.set_shipment_details(data_details)

		# Find pattern match for the shipment data
		pattern_match = self.find_pattern_match(self.get_one_pattern('shipment_data'), self.get_data_patterns())

		# Test print to see what pattern_match is
		# print(f"Pattern match: {pattern_match}")

		# Validate shipment data
		validate_check = self.validate_shipment_data(file_path, self.get_one_pattern('shipment_data'), pattern_match)

		# If validation passes grab the start index for the shipment_data dataframe
		if validate_check:
			table_start_index = pattern_match['indices'][0]

		######################################################################
		############   START OF THE COPIED CODE FROM APP READ_CSV  ###########
		######################################################################

		# Read the data into a pandas dataframe
		table_data = pd.read_csv(file_path, skiprows=table_start_index)

		# Store the dataframe into the model
		# Except this line - this isn't copied code
		self.set_shipment_data(table_data)

		mask = table_data['Box ID'].str.contains(',') & (table_data['Total units'] > 1)
		multi_shipment_rows = table_data[mask].copy()

		multi_shipment_rows['Box ID'] = multi_shipment_rows['Box ID'].str.split(',')
		exploded_rows = multi_shipment_rows.explode('Box ID')
		exploded_rows['Total units'] = 1

		table_data = pd.concat([table_data[~mask], exploded_rows])

		# Shipment details from the model
		shipment_details_data = self.get_shipment_details()
		shipment_id = shipment_details_data['Shipment ID']
		shipment_name = shipment_details_data['Shipment name']

		# Parse the date
		date_match = re.search(r'\((\d{2}/\d{2}/\d{4})', shipment_name)
		date_str = date_match.group(1) if date_match else ''

		if date_str:
			date_obj = datetime.strptime(date_str, "%d/%m/%Y")
			formatted_date = date_obj.strftime("%m/%d/%Y")
		else:
			formatted_date = None

		table_data['Shipment ID'] = shipment_id
		table_data['Date'] = formatted_date

		self.set_shipment_data(table_data)
		print("Shipment data read successful")



if __name__ == '__main__':
	model = Model()

	# Set file paths for testing
	test_csv_path = "C:/Users/lange/Downloads/FBA17FD3Y0G2.csv"
	test_pdf_path = "C:/Users/lange/Downloads/package-FBA17FD3Y0G2.pdf"

	# Set CSV and PDF records for testing
	model.set_csv_record(test_csv_path)
	model.set_pdf_record(test_pdf_path)

	model.read_csv()