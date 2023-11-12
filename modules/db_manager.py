import sqlite3

# Database Class
class DBManager:
	def __init__(self, db_path):
		self.db_path = db_path
		self.conn = None
		self.cursor = None

	def connect(self):
		self.conn = sqlite3.connect(self.db_path)
		self.cursor = self.conn.cursor()

	def close(self):
		self.conn.close()

	def setup_tables(self):
		# Database table structure - shipment table
		self.cursor.execute(''' CREATE TABLE IF NOT EXISTS shipments (
			shipment_id TEXT PRIMARY KEY,
			workflow_name TEXT,
			shipment_name TEXT,
			ship_to TEXT,
			boxes INTEGER,
			skus INTEGER,
			units INTEGER,
			timestamp DATETIME
		); ''')

		# Line item table
		self.cursor.execute(''' CREATE TABLE IF NOT EXISTS line_items (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			shipment_id TEXT,
			sku TEXT,
			asin TEXT,
			fnsku TEXT,
			box_id TEXT,
			pdf_hash TEXT,
			distributed_on DATETIME,
			workorder_id TEXT,
			active_pdf_path TEXT,
			archived_pdf_path TEXT,
			FOREIGN KEY (shipment_id) REFERENCES shipments (shipment_id)
		); ''')

		# CSV archive table
		self.cursor.execute(''' CREATE TABLE IF NOT EXISTS csv_archives (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			shipment_id TEXT,
			file_name TEXT,
			csv_blob BLOB,
			archived_on DATETIME DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (shipment_id) REFERENCES shipments (shipment_id)
		); ''')
		self.conn.commit()

	def archive_csv(self, shipment_id, file_path):
		with open(file_path, 'rb') as file:
			csv_blob = file.read()
		self.cursor.execute('''
			INSERT INTO csv_archives (shipment_id, file_name, csv_blob)
			VALUES (?, ?, ?)
		''', (shipment_id, os.path.basename(file_path), csv_blob))
		self.conn.commit()