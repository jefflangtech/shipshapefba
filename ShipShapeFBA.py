##########################
###   MAIN APP CLASS   ###
##########################

from modules.model import Model
from modules.view import View
import os


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
		

	# Function for processing the loaded files
	def process_files(self):
		
		# Process the csv file
		self.model.read_csv()

		# Verify pdf file and csv files match
		if self.model.verify_data_match():
			print("Files match!")

			# Split the labels and store by sku
			self.model.split_shipment_labels()

			# Write out the organized csv
			self.model.write_csv_to_main()

		else:
			print("Error in files: check for match")



	def print_status(self):
		print(f"App is live!")

	def run(self):
		self.view.run()


# Run the app!
app = ShipShapeFBA()
app.run()