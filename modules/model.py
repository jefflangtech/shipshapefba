##########################
###   MODEL CLASS  ###
##########################

from .db_manager import DBManager
from .record_types import PDFRecord, CSVRecord

### Copied imports from the app file ###
import csv


class Model:
	def __init__(self):
		self._files = [None, None]
		self._db = None
		self._patterns = None
		# Attributes for the csv data scan
		self._data_patterns = None
		self._max_scan_rows = 100
		# Attributes for the shipment data
		self._shipment_details = None
		self._shipment_data = None
		self._shipment_labels = None
		if not self._db:
			self.initialize_db()
		if not self._patterns:
			self.initialize_patterns()


	# Set up the database
	def initialize_db(self):
		self._db = DBManager('app/shipshape.db')
		self._db.connect()
		self._db.setup_tables()
		self._db.close()

	# Set up the data patterns
	def initialize_patterns(self):
		self._patterns = {
			'shipment_details': {
				'rows': 1,
				'cols': 2,
				'orientation': 'rows',
				'fixed': 'cols',
				'labels': ['shipment id', 'shipment name', 'boxes', 'units']
			},
			'shipment_data': {
				'rows': 2,
				'cols': 3,
				'orientation': 'cols',
				'fixed': None,
				'labels': ['sku', 'total boxes', 'total units', 'box id']
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

		for index, pattern in enumerate(data_patterns):
			if fixed_dim:
				if pattern['size'][size[fixed_dim]] == to_match[fixed_dim]:
					matches.append(pattern)
		
		# Right now this only looks for shipment details
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
		
		labels_array = data_pattern['labels']

		# Initialize labels match to False
		validate = False

		# Loop through all the labels
		for label in labels_array:
			match = False
			# Loop through the keys to see if there is a match
			for key in data:
				if key.lower() == label.lower():
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
	def read_csv(self):

		file_path = self.get_csv_record().get_path()

		# Identify the data patterns in the csv file and store them
		patterns = self.find_data_patterns(file_path)
		self.set_data_patterns(patterns)

		# Look for a match
		# This result matches the shipment details data
		pattern_match = self.find_pattern_match(self.get_one_pattern('shipment_details'), self.get_data_patterns())

		# Pull the data according to the matched pattern
		data_details = self.read_shipment_details(file_path, pattern_match)

		# Validate the data matches expected key details
		validate_check = self.validate_shipment_details(data_details, self.get_one_pattern('shipment_details'))

		# If validation passes store the shipment details
		if validate_check:
			self.set_shipment_details(data_details)



if __name__ == '__main__':
	model = Model()

	# Set file paths for testing
	test_csv_path = "C:/Users/lange/Downloads/FBA17FD3Y0G2-TESTING.csv"
	test_pdf_path = "C:/Users/lange/Downloads/package-FBA17FD3Y0G2.pdf"

	# Set CSV and PDF records for testing
	model.set_csv_record(test_csv_path)
	model.set_pdf_record(test_pdf_path)

	model.read_csv()