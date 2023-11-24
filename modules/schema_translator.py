import json

class SchemaTranslator:

	def __init__(self, schema_definition):
		self._schema_definition = schema_definition

		self.sqlite_type_mapping = {
			"number": "INTEGER",
			"string": "TEXT",
			"datetime": "DATETIME",
			"binary": "BLOB"
		}


	# Translate the generic scheme type using the database specific type map
	def translate_type(self, type_map, generic_type):
		return type_map.get(generic_type, "TEXT")


	# Generate Sqlite3 database initialization statements
	def translate_sqlite(self):
		type_map = self.sqlite_type_mapping

		sql_statements = []
		for table_name, table_def in self._schema_definition['tables'].items():

			column_defs = []
			for col_name, col_type in table_def['columns'].items():

				# translate the generic types to the sqlite types
				db_type = self.translate_type(type_map, col_type)
				column_def = f"{col_name} {db_type}"

				# Check if column is a single primary key
				if 'primary_key' in table_def and len(table_def['primary_key']) == 1 and col_name == table_def['primary_key'][0]:
						column_def += " PRIMARY KEY"
				
				# Check for auto_increment primary key
				if 'auto_increment' in table_def and col_name in table_def['auto_increment']:
						column_def += " AUTOINCREMENT"

				column_defs.append(column_def)

			# Append primary key definition for composite primary keys
			if 'primary_key' in table_def and len(table_def['primary_key']) > 1:
					pk_def = "PRIMARY KEY (" + ", ".join(table_def['primary_key']) + ")"
					column_defs.append(pk_def)

			# Append foreign key definitions
			if 'foreign_keys' in table_def:
					fk_defs = [f"FOREIGN KEY ({fk_col}) REFERENCES {ref_table}" for fk_col, ref_table in table_def['foreign_keys'].items()]
					column_defs.extend(fk_defs)

			table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)});"
			sql_statements.append(table_sql)

		return sql_statements
	


if __name__ == '__main__':
	file_path = 'app/schema.json'

	schema = SchemaTranslator(file_path)
	statements = schema.translate_sqlite()

	print(statements[0])
	print()
	print(statements[1])
	print()
	print(statements[2])