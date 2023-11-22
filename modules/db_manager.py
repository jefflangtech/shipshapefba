from abc import ABC, abstractmethod

# Database Class
class DBManager(ABC):

	@abstractmethod
	def connect(self):
		pass

	@abstractmethod
	def close(self):
		pass

	@abstractmethod
	def load_schema(self):
		pass

	@abstractmethod
	def setup_tables(self):
		pass