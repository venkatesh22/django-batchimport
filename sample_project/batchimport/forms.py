from django import forms
from util import get_model_list, get_column_choice_list, get_model_fields
from batchimport_settings import *
from django.forms.forms import BoundField


model_list = get_model_list()

class UploadImportFileForm(forms.Form):
	model_for_import = forms.ChoiceField(model_list, label='What are you importing?')
	import_file = forms.FileField(label='Select your XLS file:')

class ImportOptionsForm(forms.Form):
	show_successful_imports = forms.BooleanField(initial=BATCH_IMPORT_SHOW_SUCCESSFUL_IMPORTS, required=False)
	show_successful_updates = forms.BooleanField(initial=BATCH_IMPORT_SHOW_SUCCESSFUL_UPDATES, required=False)
	show_errors = forms.BooleanField(initial=BATCH_IMPORT_SHOW_ERRORS, required=False)
	stop_on_first_error = forms.BooleanField(initial=BATCH_IMPORT_STOP_ON_FIRST_ERROR, required=False)
	update_dupes = forms.BooleanField(initial=BATCH_IMPORT_UPDATE_DUPS, required=False)
	start_row = forms.IntegerField(initial=BATCH_IMPORT_START_ROW, required=False)
	end_row = forms.IntegerField(initial=BATCH_IMPORT_END_ROW, required=False)
	
	def __init__(self, model_for_import, save_file_name, *args, **kwargs):
		super(ImportOptionsForm, self).__init__(*args, **kwargs)
        # Get a list of columns from the uploaded spreadsheet.
		# This will be either a list of example values or a list
		# of column headers.
		xls_column_option_list = get_column_choice_list(save_file_name)
		
		# Get a list of field names from the selected model
		# for import.
		model_field_tuple_list = get_model_fields(model_for_import)
		
		# Then iterate over the names of the model fields.
		# For each one, create a form field for the 
		# list of possible xls columns, a field for a default value,
		# a field for a mapping list, if needed, and a boolean
		# field for whether this model field is part of a "key."
		self.field_dict = {}
		self.related_model_dict = {}
		for field_tuple in model_field_tuple_list:
			field_name = field_tuple[0]
			related_model_app_name = field_tuple[1]
			related_model_name = field_tuple[2]
			field_mapping_list = field_tuple[3]
			form_field_list = []
			related_field_choice_list = []
			if len(field_mapping_list) > 0:
				for related_field_name in field_mapping_list:
					related_field_choice_list.append((related_field_name, related_field_name))
			
			self.related_model_dict[field_name]= (related_model_app_name, related_model_name)

			xls_column_field_name = field_name + '_xls_column'
			self.fields[xls_column_field_name] = forms.ChoiceField(xls_column_option_list, label='Spreadsheet column:', required=False, initial='-1')
			form_field_list.append(xls_column_field_name)
			
			default_value_field_name = field_name + '_default_value'
			self.fields[default_value_field_name] = forms.CharField(label="Default value", max_length=100, required=False)
			form_field_list.append(default_value_field_name)
			
			mapping_choice_field_name = field_name + '_mapping_choice'
			self.fields[mapping_choice_field_name] = forms.ChoiceField(related_field_choice_list, label='Related model field mapping', required=False)
			form_field_list.append(mapping_choice_field_name)
			
			is_id_field_name = field_name + '_is_id_field'
			self.fields[is_id_field_name] = forms.BooleanField(required=False,initial=True)
			form_field_list.append(is_id_field_name)

			self.field_dict[field_name] = form_field_list
			