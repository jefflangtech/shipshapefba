########################
###    VIEW CLASS    ###
########################

import customtkinter as ctk
from tkinter import filedialog

# App appearance
ctk.set_appearance_mode("System")  # Modes: system (default), light, dark
ctk.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green

class View(ctk.CTk):

	def __init__(self, controller):
		super().__init__()
		self.controller = controller
		self.title('ShipShapeFBA')
		self.iconbitmap('app/favicon.ico')
		self.geometry("800x600")
		self.setup_gui()

	# Utility method to update the text for a label
	def update_label(self, label, msg):
		label.configure(text=f"{msg}")

	def file_picker(self, file_type, callback, gui_element):

		switch = {
			'CSV': {
				'title': f'Select Shipment Details CSV File',
				'type': [("CSV files", "*.csv")]
			},
			'PDF': {
				'title': f'Select Shipment Labels PDF File',
				'type': [("PDF files", "*.pdf")]
			}

		}

		file_path = filedialog.askopenfilename(
				title = switch[file_type]['title'],
				filetypes = switch[file_type]['type']
			)
		if file_path:
			msg = self.controller.update_record(file_path)

		msg = f'File selected: {msg}'

		callback(gui_element, msg)

	# Initialize the gui elements
	def setup_gui(self):
		# Labels
		self.csv_file_label = ctk.CTkLabel(self, text="No CSV file selected")
		self.pdf_file_label = ctk.CTkLabel(self, text="No PDF file selected")

		# Buttons
		self.open_csv_button = ctk.CTkButton(self, text="Load FBA Shipment File", command=lambda: self.file_picker(
			"CSV", 
			self.update_label, 
			self.csv_file_label
		))
		self.open_pdf_button = ctk.CTkButton(self, text="Load Shipment Labels File", command=lambda: self.file_picker(
			"PDF",
			self.update_label,
			self.pdf_file_label
		))

		# Arrange on GUI grid
		self.open_csv_button.grid(row=0, column=0, padx=30, pady=40)
		self.open_pdf_button.grid(row=1, column=0, padx=30, pady=0)
		self.csv_file_label.grid(row=0, column=1, padx=40, pady=40)
		self.pdf_file_label.grid(row=1, column=1, padx=40, pady=0)

		# Button to initiate processing the files
		self.process_button = ctk.CTkButton(self, text="Process", command=self.controller.process_files)
		self.process_button.grid(row=2, column=0, padx=30, pady=50)

	def run(self):
		self.mainloop()