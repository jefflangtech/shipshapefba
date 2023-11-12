from .record import Record

# PDFRecord subclass
class PDFRecord(Record):
	def __init__(self, file_path=None):
		super().__init__(file_path)

	def process_pdf(self):
		# Method to process pdf specific details
		pass

# CSVRecord subclass
class CSVRecord(Record):
	def __init__(self, file_path=None):
		super().__init__(file_path)

	def process_csv(self):
		# Method to process csv specific details
		pass