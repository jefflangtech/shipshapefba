from .db_manager import DBManager
import sqlite3

class SqliteManager(DBManager):
	def __init__(self, db_path, schema_translator):
		self.db_path = db_path
		self.db_schema = schema_translator
		self.conn = None
		self.cursor = None

	def connect(self):
		self.conn = sqlite3.connect(self.db_path)
		self.cursor = self.conn.cursor()


	def close(self):
		self.conn.close()


	def load_schema(self):
		return self.db_schema.translate_sqlite()


	def setup_tables(self):

		schema = self.load_schema()

		for sql in schema:
			self.cursor.execute(f''' {sql} ''')


	def archive_csv(self, shipment_id, file_path):
		with open(file_path, 'rb') as file:
			csv_blob = file.read()
		self.cursor.execute('''
			INSERT INTO csv_archives (shipment_id, file_name, csv_blob)
			VALUES (?, ?, ?)
		''', (shipment_id, os.path.basename(file_path), csv_blob))
		self.conn.commit()