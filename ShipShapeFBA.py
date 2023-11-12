from PyPDF2 import PdfWriter, PdfReader
import pandas as pd
import csv
import re
from datetime import datetime
import os
from modules.model import Model
from modules.view import View

##############################################################
# NEXT TO DO'S
# Finish reading the units data into the model (read_csv methods),
# then work on refactoring the pandas code, probably splitting
# that into a separate method since read_csv is getting huge
##############################################################

# Globals -- need to convert to object attributes
shipment_data = None
shipment_labels = None

##########################
###   MAIN APP CLASS   ###
##########################
class ShipShapeFBA:

	def __init__(self):
		self.model = Model()
		self.view = View(self)

	def update_record(self, file_path):

		ext = os.path.splitext(file_path)[1]
		switch = {
			'.csv': self.model.set_csv_record,
			'.pdf': self.model.set_pdf_record
		}

		record = switch[ext](file_path)
		msg = record.get_basename()

		return msg

	#################################################################
	# # #   Start copied code
	#################################################################

	# Utility function to locate the start of the line item table in the csv
	def find_table_start_index(self, file_path):
		with open(file_path, 'r', newline='') as file:
			reader = csv.reader(file)
			for index, row in enumerate(reader):
				if all(not cell.strip() for cell in row):
					# Found the blank row
					try:
						# Check for a title row
						next_row = next(reader)
						if(next_row[0].strip() and all(not cell.strip() for cell in next_row[1:])):
							# Found the title row
							return index + 2
					except StopIteration:
						break
					# No title row
					return index + 1
		return None


	def read_csv(self):

		global shipment_data

		table_start_index = self.find_table_start_index(self.model.get_csv_record().get_path())
		print(f"Table start index: {table_start_index}")

		# Read the primary data table from the shipment
		shipment_data = pd.read_csv(self.model.get_csv_record().get_path(), skiprows=table_start_index)

		mask = shipment_data['Box ID'].str.contains(',') & (shipment_data['Total units'] > 1)
		multi_shipment_rows = shipment_data[mask].copy()

		multi_shipment_rows['Box ID'] = multi_shipment_rows['Box ID'].str.split(',')
		exploded_rows = multi_shipment_rows.explode('Box ID')
		exploded_rows['Total units'] = 1

		shipment_data = pd.concat([shipment_data[~mask], exploded_rows])

		# Shipment details from the model
		shipment_details_data = self.model.get_shipment_details()
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

		shipment_data['Shipment ID'] = shipment_id
		shipment_data['Date'] = formatted_date

		print("Shipment data read successful")


	def write_csv_to_main(self):

		global shipment_data

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


	def verify_data_match(self):

		global shipment_data
		global shipment_labels

		with open(self.model.get_pdf_record().get_path(), 'rb') as file:
			shipment_labels = PdfReader(file)

			# Box quantity verification check
			# Shipment details from the model
			shipment_details_data = self.model.get_shipment_details()
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

	def split_ship_labels(self):

		global shipment_data
		global shipment_labels

		with open(self.model.get_pdf_record().get_path(), 'rb') as file:
			shipment_labels = PdfReader(file)

			# Sort shipment data by box ID
			sorted_data = shipment_data.sort_values(by='Box ID')

			# Set page index for pdf labels file
			pdf_page_index = 0

			# Set current sku
			current_sku = None

			writer = PdfWriter()
			for _, row in sorted_data.iterrows():
				sku = row['SKU']

				if not current_sku:
					# Just started reading, set up for new pdf file
					current_sku = sku

				elif current_sku and (current_sku != sku):
					# New sku set reached, write out current pdfs pages to file
					file_loc = f'files/pdfs/consolidated/{current_sku.strip()}.pdf'
					# Write out the PDF
					with open(file_loc, 'wb') as f:
						writer.write(f)
						writer.close()
					current_sku = sku
					writer = PdfWriter()

				writer.add_page(shipment_labels.pages[pdf_page_index])
				writer.add_page(shipment_labels.pages[pdf_page_index + 1])
				pdf_page_index += 2

			# Final file write as the loop ends
			file_loc = f'files/pdfs/consolidated/{current_sku.strip()}.pdf'
			with open(file_loc, 'wb') as f:
				writer.write(f)
				writer.close()

	# Function for processing the loaded files
	def process_files(self):
		
		# Process the csv file
		self.model.read_csv()

		# Model method is halfway re-factored. Finish the job here
		self.read_csv()

		# Verify pdf file and csv files match
		if self.verify_data_match():
			print("Files match!")

			# Split the labels and store by sku
			self.split_ship_labels()

			# Write out the organized csv
			self.write_csv_to_main()

		else:
			print("Error in files: check for match")



	def print_status(self):
		print(f"App is live!")

	def run(self):
		self.view.run()


# Run the app!
app = ShipShapeFBA()
app.run()