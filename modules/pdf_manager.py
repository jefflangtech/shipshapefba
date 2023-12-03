from PyPDF2 import PdfReader, PdfWriter, PdfMerger
import os
from io import BytesIO
import hashlib

# PDF File Manager Class
class PDFManager:
	def __init__(self, base_directory):
		self._base_directory = base_directory
		self._active_directory = os.path.join(self._base_directory, f"consolidated/")
		self._archive_directory = os.path.join(self._base_directory, f"originals/")


  ########### SETTERS ##############



  ########### GETTERS ##############
	def get_base_dir(self):
		return self._base_directory

	def get_active_dir(self):
		return self._active_directory

	def get_archive_dir(self):
		return self._archive_directory

	########### CLASS METHODS ##############
	def get_file_path(self, sku, is_active):

		if is_active:
			return os.path.join(self._active_directory, f"{sku}.pdf")
		elif not is_active:
			return os.path.join(self._archive_directory, f"{sku}.pdf")

		return None
	

	def file_exists(self, sku, is_active=True):
		file_path = self.get_file_path(sku, is_active)
		return os.path.exists(file_path)

	
	def read_pdf(self, file_path):
		pdf_pages = []
		with open(file_path, 'rb') as file:
			reader = PdfReader(file)
			for page in reader.pages:
				pdf_pages.append(page)
				return pdf_pages


	def write_pdf(self, pdf_writer, file_path):
		with open(file_path, 'wb') as out_file:
			pdf_writer.write(out_file)


	def append_to_pdf(self, existing_pdf, new_pdf, page_range=()):

		merger = PdfMerger(existing_pdf)

		merger.append(existing_pdf)
		merger.append(new_pdf, pages=page_range)

		merger.write(existing_pdf)
		merger.close()

	
	# Takes the new pdf pages and the sku, and a boolean is_active to direct
	# the pages to active labels or archived labels. Default is active
	def process_pdf_pages(self, new_pages, sku, is_active=True, page_range=()):

		if self.file_exists(sku, is_active):
			existing_pdf_path = self.get_file_path(sku, is_active)
			self.append_to_pdf(existing_pdf_path, new_pages, page_range)
		else:
			pdf_merger = PdfMerger()
			pdf_merger.append(new_pages, pages=page_range)
			new_pdf_path = self.get_file_path(sku, is_active)
			pdf_merger.write(new_pdf_path)
			pdf_merger.close()


	def generate_pdf_hash(self, pages):
		
		writer = PdfWriter()

		# # Get binary data from the text
		# text_data = pages[0].encode()

		# # Get binary data from the shipping label page
		# writer.add_page(pages[1])

		for page in pages:
			writer.add_page(page)

		with BytesIO() as bytes_stream:
			writer.write(bytes_stream)
			page_data = bytes_stream.getvalue()

		# combined_data = text_data + image_page_data

		hash_object = hashlib.sha256()
		hash_object.update(page_data)

		return hash_object.hexdigest()


if __name__ == '__main__':
	pdf_mgr = PDFManager('files/pdfs/')
	
	print(f"Base dir: {pdf_mgr.get_base_dir()}")
	print(f"Active dir: {pdf_mgr.get_active_dir()}")
	print(f"Archive dir: {pdf_mgr.get_archive_dir()}")