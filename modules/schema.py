from abc import ABC, abstractmethod
import json

# Abstract inteface class defining a schema loader for the database
class ISchemaLoader(ABC):

	@abstractmethod
	def load_schema(self):
		pass


# Interface class for loading a schema from a JSON file
class FileSchemaLoader(ISchemaLoader):
	def __init__(self, file_path):
		self._file_path = file_path


	def load_schema(self):
		with open(self._file_path, 'r') as file:
			schema = json.load(file)
		return schema


# Interface class for loading a schema from an API endpoint
class APISchemaLoader(ISchemaLoader):
	def __init__(self, file_path):
		self._file_path = file_path


  # FIXME: this should be logic for loading a json schema from an API
	def load_schema(self):
		with open(self._file_path, 'r') as file:
			schema = json.load(file)
		return schema


# Logic for loading and validating the schema
class SchemaLoader:
  def __init__(self, loader: ISchemaLoader):
    self.loader = loader


  def load_and_validate_schema(self):
    schema = self.loader.load_schema()

    # TO-DO: create validation logic for schema

    return schema