import os

# Record super class
class Record:
	def __init__(self, file_path=None):
		self.file_path = file_path
		self.file_name = None
		self.file_ext = None
		if file_path:
			self.process_file_path()

	def process_file_path(self):
		self.file_name, self.file_ext = os.path.splitext(os.path.basename(self.file_path))

	def does_exist(self):
		if os.path.exists(self.file_path):
			return True

	def get_size(self):
		return os.path.getsize(self.file_path)
	
	def set_path(self, file_path):
		self.file_path = file_path
		if self.file_path:
			self.process_file_path()

	def get_path(self):
		return self.file_path

	def get_basename(self):
		return os.path.basename(self.file_path)

	def get_ext(self):
		return self.file_ext