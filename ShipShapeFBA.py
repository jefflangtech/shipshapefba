##########################
###   MAIN APP CLASS   ###
##########################

from modules.model import Model
from modules.view import View
from modules.config_loader import load_config
from modules.schema_translator import SchemaTranslator
from modules.schema import SchemaLoader, FileSchemaLoader, APISchemaLoader
from modules.sqlite_manager import SqliteManager
from modules.utils import Utils as utils
import os


class ShipShapeFBA:

	def __init__(self):
		self.config = load_config()
		self.model = Model(self.config)
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


	def configure_db_schema(self, path):

		# Select API or local File loaders
		if utils.is_remote_path(path):
			schema_data = APISchemaLoader(path)

		elif utils.is_local_path(path):
			schema_data = FileSchemaLoader(path)

		schema_loader = SchemaLoader(schema_data)
		schema = schema_loader.load_and_validate_schema()

		return schema


	def configure_application(self):

		# Database configuration
		db_config = self.config['database']

		# Get the schema
		schema = self.configure_db_schema(db_config['schema_path'])

		# Configure schema translator
		schema_translator = SchemaTranslator(schema)

		# Configure database
		db = SqliteManager(db_config['path'], schema_translator)
		db.connect()
		db.setup_tables()
		db.close()
		


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
app.configure_application()
app.run()