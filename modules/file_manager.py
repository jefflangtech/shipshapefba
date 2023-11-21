import queue

class FileManager:
	_instance = None

	def __new__(cls, *args, **kwargs):
		if cls._instance is None:
			cls._instance = super(FileManager, cls).__new__(cls, *args, **kwargs)
		return cls._instance

	def __init__(self):
		self.	_queue = queue.Queue()



if __name__ == '__main__':
	file_mgr1 = FileManager()
	file_mgr2 = FileManager()

	if file_mgr1 is file_mgr2:
		print(f"'Tis true")